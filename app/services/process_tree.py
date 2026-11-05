from collections import defaultdict

from app.core.errors import ToolError
from app.schemas.process_tree import ProcessTreeOptions
from app.utils import get_field, json_result, read_records


# Construct host-scoped GUID relationships without guessing links from reused PIDs.
def build_process_tree(options: ProcessTreeOptions) -> dict:
    records = read_records(options.text, options.format)
    nodes, by_guid, warnings = [], {}, []
    for index, record in enumerate(records):
        host = str(get_field(record, options.host_field) or "")
        guid = str(get_field(record, options.guid_field) or "")
        parent_guid = str(get_field(record, options.parent_field) or "")
        if max(map(len, (host, guid, parent_guid))) > 256:
            raise ToolError("Process identifiers and host labels are limited to 256 characters.")
        node = {
            "record_index": index + 1,
            "host": host,
            "guid": guid,
            "parent_guid": parent_guid,
            "pid": get_field(record, options.pid_field),
            "image": get_field(record, options.image_field),
            "command_line": get_field(record, options.command_field),
            "parent_index": None,
        }
        nodes.append(node)
        if guid:
            key = (host, guid)
            if key in by_guid:
                raise ToolError(
                    "Duplicate host/ProcessGuid records are ambiguous; deduplicate explicitly first."
                )
            by_guid[key] = index
    for node in nodes:
        if not node["guid"]:
            node["relationship_warning"] = "No ProcessGuid; PID-only parentage is unresolved."
        elif node["parent_guid"]:
            parent = by_guid.get((node["host"], node["parent_guid"]))
            if parent is None:
                node["relationship_warning"] = (
                    "Parent GUID is absent from the supplied host records."
                )
            else:
                node["parent_index"] = parent
    completed = set()
    for index in range(len(nodes)):
        chain, positions, current = [], set(), index
        while current is not None and current not in completed:
            if current in positions:
                nodes[current]["parent_index"] = None
                nodes[current]["relationship_warning"] = (
                    "Cycle detected; this parent edge was refused."
                )
                warnings.append("A cyclic relationship was broken explicitly.")
                break
            positions.add(current)
            chain.append(current)
            current = nodes[current]["parent_index"]
        completed.update(chain)
    if options.export == "json":
        return json_result(nodes, {"processes": len(nodes)}, warnings)
    children, roots = defaultdict(list), []
    for index, node in enumerate(nodes):
        if node["parent_index"] is None:
            roots.append(index)
        else:
            children[node["parent_index"]].append(index)
    lines, shown = [], 0
    pending = [(index, 0) for index in reversed(roots)]
    while pending:
        index, depth = pending.pop()
        node = nodes[index]
        label = str(node["image"] or "(unknown image)")[:256]
        label = label.replace("\r", "\\r").replace("\n", "\\n")
        lines.append(
            "  " * depth + f"↳ {label} [PID {node['pid']}, host {node['host'] or '(not supplied)'}]"
        )
        shown += 1
        if node.get("relationship_warning"):
            lines.append("  " * min(depth + 1, 64) + "! " + node["relationship_warning"])
        if depth >= 64 and children[index]:
            lines.append(
                "  " * 64 + "… further depth omitted; select JSON export for all relationships"
            )
            continue
        pending.extend((child, depth + 1) for child in reversed(children[index]))
    return {
        "output": "\n".join(lines),
        "meta": {"processes": len(nodes), "shown": shown},
        "warnings": warnings
        + [
            "GUIDs are correlated within supplied host labels. No PID-only parent links are invented. JSON export preserves all node relationships."
        ],
    }

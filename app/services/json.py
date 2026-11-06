from decimal import Decimal
from typing import Any

import jmespath
from jmespath.exceptions import JMESPathError

from app.core.documents import (
    DuplicateKey,
    check_nodes,
    child_pointer,
    dump_document,
    load_document,
    scalar_label,
)
from app.core.errors import ToolError
from app.schemas.json import JsonOptions

SAFE_QUERY_NODES = {
    "field",
    "subexpression",
    "index",
    "index_expression",
    "projection",
    "flatten",
    "identity",
    "slice",
    "value_projection",
    "current",
}


# Produce a typed tree whose scalar labels preserve exact values in JavaScript.
def tree_node(value: Any, key: str = "$", path: str = "", budget: list[int] | None = None) -> dict:
    if budget is None:
        budget = [0]
    label = "" if isinstance(value, (dict, list)) else scalar_label(value)
    budget[0] += (
        len(key.encode("utf-8")) + len(path.encode("utf-8")) + len(label.encode("utf-8")) + 128
    )
    if budget[0] > 4 * 1024 * 1024:
        raise ToolError("JSON tree exceeds its 4 MiB construction budget.", "work_limit", 413)
    if isinstance(value, dict):
        children = [
            tree_node(item, name, child_pointer(path, name), budget) for name, item in value.items()
        ]
        return {
            "key": key,
            "path": path,
            "kind": "object",
            "count": len(value),
            "children": children,
        }
    if isinstance(value, list):
        return {
            "key": key,
            "path": path,
            "kind": "array",
            "count": len(value),
            "children": [
                tree_node(item, str(i), child_pointer(path, str(i)), budget)
                for i, item in enumerate(value)
            ],
        }
    kind = (
        "string"
        if isinstance(value, str)
        else "number"
        if type(value) in {int, float, Decimal}
        else "value"
    )
    return {"key": key, "path": path, "kind": kind, "value": scalar_label(value)}


# Evaluate only bounded field/index/wildcard projections, not arbitrary expression expansion.
def project(value: Any, expression: str) -> Any:
    if not expression:
        raise ToolError("Enter a JMESPath field/index/wildcard expression.")
    try:
        query = jmespath.compile(expression)
        pending = [query.parsed]
        while pending:
            node = pending.pop()
            if node["type"] not in SAFE_QUERY_NODES:
                raise ToolError(
                    "Use field, index, slice, or wildcard projections; functions and constructed objects are not enabled."
                )
            pending.extend(child for child in node.get("children", []) if isinstance(child, dict))
        result = query.search(value)
    except (JMESPathError, ValueError, TypeError) as exc:
        raise ToolError("Invalid JMESPath projection.") from exc
    check_nodes(result)
    return result


# Inspect JSON without silently rounding numbers, deleting duplicates, or repairing syntax.
def inspect_json(options: JsonOptions) -> dict:
    source, meta, warnings = options.text, {}, []
    if options.format == "jsonl":
        records = [(i, line) for i, line in enumerate(source.splitlines(), 1) if line.strip()]
        if len(records) > 5000:
            raise ToolError("JSONL is limited to 5,000 records.", "work_limit", 413)
        if options.record > len(records):
            raise ToolError("Selected record is outside the JSONL input.")
        line, source = records[options.record - 1]
        meta.update(records=len(records), source_line=line)
        warnings.append("Only the selected nonblank JSONL record is inspected and exported.")
    try:
        document = load_document(source)
    except DuplicateKey:
        return {
            "output": source,
            "meta": {"duplicate_keys": True},
            "data": {"tree": None},
            "warnings": [
                "Duplicate object keys detected. Raw input is preserved; formatting and projection are disabled."
            ],
        }
    if options.action == "query":
        document = project(document, options.query)
        warnings.append(
            "Output is the explicitly requested projection, not the full source document."
        )
    output = dump_document(document, pretty=options.action != "minify")
    pending = [document]
    counts = {"objects": 0, "arrays": 0, "scalars": 0}
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            counts["objects"] += 1
            pending.extend(item.values())
        elif isinstance(item, list):
            counts["arrays"] += 1
            pending.extend(item)
        else:
            counts["scalars"] += 1
    meta.update(counts)
    meta["output_characters"] = len(output)
    return {
        "output": output,
        "extension": "json",
        "meta": meta,
        "warnings": warnings,
        "data": {"tree": tree_node(document), "compact": dump_document(document, pretty=False)},
    }

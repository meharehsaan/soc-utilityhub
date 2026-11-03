import difflib
from typing import Any

from app.core.documents import DuplicateKey, child_pointer, dump_document, load_document
from app.core.errors import ToolError
from app.schemas.compare import CompareOptions


# Index unique list items by explicit comparison rules while retaining the original spelling.
def index_lines(text: str, options: CompareOptions) -> dict[str, str]:
    values = text.splitlines()
    if len(values) > 20000:
        raise ToolError("List comparison is limited to 20,000 lines per input.", "work_limit", 413)
    result = {}
    for value in values:
        key = value.strip() if options.trim else value
        if not options.case_sensitive:
            key = key.casefold()
        result.setdefault(key, value)
    return result


# Cap cumulative diff text before repeated paths or removed subtrees consume memory.
def append_change(changes: list[str], message: str) -> None:
    if len(changes) >= 2000 or sum(map(len, changes)) + len(message) > 512 * 1024:
        raise ToolError("Structural diff exceeds its bounded output budget.", "work_limit", 413)
    changes.append(message)


# Compare JSON types, values, and ordered array positions with bounded change reporting.
def json_changes(a: Any, b: Any, changes: list[str], ignore_order: bool, path: str = "$") -> None:
    if len(changes) >= 2000:
        raise ToolError(
            "More than 2,000 structural changes; narrow the documents.", "work_limit", 413
        )
    if type(a) is not type(b) and not (
        type(a).__name__ in {"int", "Decimal"} and type(b).__name__ in {"int", "Decimal"}
    ):
        append_change(
            changes, f"{path}: {dump_document(a, pretty=False)} → {dump_document(b, pretty=False)}"
        )
    elif isinstance(a, dict):
        if not ignore_order and list(a) != list(b):
            append_change(changes, f"{path}: object key order differs")
        for key in a:
            pointer = child_pointer(path, key)
            if key not in b:
                append_change(changes, f"{pointer}: removed {dump_document(a[key], pretty=False)}")
            else:
                json_changes(a[key], b[key], changes, ignore_order, pointer)
            if len(changes) >= 2000:
                raise ToolError(
                    "More than 2,000 structural changes; narrow the documents.", "work_limit", 413
                )
        for key in b:
            if key not in a:
                append_change(
                    changes,
                    f"{child_pointer(path, key)}: added {dump_document(b[key], pretty=False)}",
                )
                if len(changes) >= 2000:
                    raise ToolError(
                        "More than 2,000 structural changes; narrow the documents.",
                        "work_limit",
                        413,
                    )
    elif isinstance(a, list):
        for i in range(max(len(a), len(b))):
            if i >= len(a):
                append_change(
                    changes,
                    f"{child_pointer(path, str(i))}: added {dump_document(b[i], pretty=False)}",
                )
            elif i >= len(b):
                append_change(
                    changes,
                    f"{child_pointer(path, str(i))}: removed {dump_document(a[i], pretty=False)}",
                )
            else:
                json_changes(a[i], b[i], changes, ignore_order, child_pointer(path, str(i)))
            if len(changes) >= 2000:
                raise ToolError(
                    "More than 2,000 structural changes; narrow the documents.", "work_limit", 413
                )
    elif a != b:
        append_change(
            changes, f"{path}: {dump_document(a, pretty=False)} → {dump_document(b, pretty=False)}"
        )


# Compare two inputs using one explicit set, line-diff, or structural-JSON mode.
def compare(options: CompareOptions) -> dict:
    if options.mode == "lists":
        a, b = index_lines(options.a, options), index_lines(options.b, options)
        groups = {
            "a_only": [a[key] for key in a if key not in b],
            "b_only": [b[key] for key in b if key not in a],
            "intersection": [a[key] for key in a if key in b],
            "union": list(a.values()) + [b[key] for key in b if key not in a],
        }
        return {
            "output": "\n".join(groups[options.operation]),
            "meta": {name: len(values) for name, values in groups.items()},
        }
    if options.mode == "text":
        a, b = options.a.splitlines(), options.b.splitlines()
        if max(len(a), len(b)) > 5000:
            raise ToolError("Text diff is limited to 5,000 lines per input.", "work_limit", 413)
        output = "\n".join(
            difflib.unified_diff(a, b, fromfile="Input A", tofile="Input B", lineterm="")
        )
        if options.a.endswith("\n") != options.b.endswith("\n"):
            output += "\n[Final line break differs]"
        return {
            "output": output or "No line differences.",
            "meta": {"a_lines": len(a), "b_lines": len(b)},
            "warnings": [
                "Line comparison ignores CRLF versus LF; final-line-break differences are reported separately."
            ],
        }
    try:
        a, b = load_document(options.a), load_document(options.b)
    except DuplicateKey as exc:
        raise ToolError("Resolve duplicate JSON keys before structural comparison.") from exc
    changes = []
    json_changes(a, b, changes, options.ignore_key_order)
    return {
        "output": "\n".join(changes) or "No structural differences.",
        "meta": {"changes": len(changes)},
    }

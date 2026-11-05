from typing import Any

from app.core.documents import DuplicateKey, dump_document, load_document
from app.core.errors import ToolError


# Build a consistent readable result without storing the underlying operation.
def json_result(data: Any, meta: dict | None = None, warnings: list[str] | None = None) -> dict:
    return {"output": dump_document(data), "meta": meta or {}, "warnings": warnings or []}


# Read an exact top-level field first, then a simple dotted nested field path.
def get_field(record: dict, path: str) -> Any:
    if path in record:
        return record[path]
    value = record
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


# Read a bounded explicit record format without guessing or discarding malformed records.
def read_records(text: str, format: str = "jsonl") -> list[dict]:
    try:
        if format == "json":
            document = load_document(text)
            records = document if isinstance(document, list) else [document]
        else:
            lines = [line for line in text.splitlines() if line.strip()]
            if len(lines) > 5000:
                raise ToolError("At most 5,000 records are supported.", "work_limit", 413)
            records = [load_document(line) for line in lines]
    except DuplicateKey as exc:
        raise ToolError("Resolve duplicate keys before record analysis.") from exc
    if len(records) > 5000 or any(not isinstance(record, dict) for record in records):
        raise ToolError("Supply at most 5,000 JSON object records.")
    return records

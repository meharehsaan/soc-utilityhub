import re

from app.core.documents import dump_document
from app.core.errors import ToolError
from app.schemas.query import QueryOptions


# Generate a copy-only KQL filter with identifiers and values validated separately.
def build_query(options: QueryOptions) -> dict:
    identifier = r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
    if not re.fullmatch(identifier, options.table) or not re.fullmatch(identifier, options.field):
        raise ToolError("Use simple KQL table/field identifiers, not expressions.")
    values = list(dict.fromkeys(line for line in options.text.splitlines() if line))
    if not values or len(values) > 1000 or any(len(value) > 2048 for value in values):
        raise ToolError("Supply 1–1,000 values of at most 2,048 characters each.")
    conditions = []
    for offset in range(0, len(values), 100):
        chunk = ", ".join(
            dump_document(value, pretty=False) for value in values[offset : offset + 100]
        )
        conditions.append(f"{options.field} {options.operator} ({chunk})")
    clause = conditions[0] if len(conditions) == 1 else "(\n  " + "\n  or ".join(conditions) + "\n)"
    return {
        "output": f"{options.table}\n| where {clause}",
        "meta": {"values": len(values), "chunks": len(conditions)},
        "warnings": [
            "Query text only; nothing was executed. 'in' is exact case-sensitive membership; 'in~' is ASCII case-insensitive; has_any matches terms."
        ],
    }

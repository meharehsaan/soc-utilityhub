from decimal import Decimal
from typing import Any

import simplejson as json
from starlette.responses import Response

from app.core.errors import ToolError

MAX_NODES = 20000
MAX_DEPTH = 64


class DuplicateKey(ValueError):
    pass


# Refuse duplicate keys instead of silently dropping evidence during parsing.
def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey("Duplicate object keys; raw input must be preserved.")
        result[key] = value
    return result


# Bound nesting before handing untrusted text to a recursive JSON decoder.
def check_depth(text: str) -> None:
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise ToolError("Document nesting exceeds 64 levels.", "document_too_deep", 413)
        elif char in "]}":
            depth -= 1


# Enforce a node budget without recursively walking unlimited collections.
def check_nodes(value: Any) -> None:
    pending, count = [value], 0
    while pending:
        current = pending.pop()
        if isinstance(current, str):
            try:
                current.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ToolError("JSON contains an unpaired Unicode surrogate.") from exc
        count += 1
        if count > MAX_NODES:
            raise ToolError("Document exceeds 20,000 values.", "too_many_values", 413)
        if isinstance(current, dict):
            if len(pending) + len(current) > MAX_NODES:
                raise ToolError("Document exceeds 20,000 values.", "too_many_values", 413)
            pending.extend(current.values())
            pending.extend(current.keys())
        elif isinstance(current, list):
            if len(pending) + len(current) > MAX_NODES:
                raise ToolError("Document exceeds 20,000 values.", "too_many_values", 413)
            pending.extend(current)


# Decode strict JSON with exact integers and decimals and useful safe errors.
def load_document(text: str) -> Any:
    check_depth(text)
    try:
        value = json.loads(text, use_decimal=True, object_pairs_hook=unique_object, allow_nan=False)
    except json.JSONDecodeError as exc:
        raise ToolError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}.") from exc
    check_nodes(value)
    return value


# Serialize results without rounding decimal values or permitting non-finite numbers.
def dump_document(value: Any, *, pretty: bool = True) -> str:
    return json.dumps(
        value,
        use_decimal=True,
        ensure_ascii=False,
        allow_nan=False,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    )


# Serialize bounded API results directly to bypass lossy decimal conversion.
def respond(result: dict[str, Any]) -> Response:
    encoded = dump_document(result, pretty=False).encode("utf-8")
    if len(encoded) > 10 * 1024 * 1024:
        raise ToolError(
            "Result exceeds 10 MiB; reduce the input or selected output.", "output_too_large", 413
        )
    return Response(encoded, media_type="application/json")


# Label scalar tree values as text so browser JSON parsing cannot round evidence IDs.
def scalar_label(value: Any) -> str:
    if isinstance(value, str):
        return value
    if type(value) in {int, Decimal}:
        return str(value)
    return dump_document(value, pretty=False)

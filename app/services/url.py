import re
from urllib.parse import parse_qsl, unquote, urlsplit

import idna

from app.core.errors import ToolError
from app.schemas.url import UrlOptions
from app.utils import json_result


# Split a URL offline while keeping repeated query values and the original spelling.
def inspect_one_url(source: str, layers: int = 0) -> dict:
    value = source
    decoded = []
    for _ in range(layers):
        if re.search(r"%(?![0-9A-Fa-f]{2})", value):
            raise ToolError("Malformed percent-encoding.")
        try:
            following = unquote(value, errors="strict")
        except UnicodeDecodeError as exc:
            raise ToolError("Percent-encoded bytes are not valid UTF-8.") from exc
        decoded.append(following)
        if following == value:
            break
        value = following
    try:
        parts = urlsplit(value)
        host, port = parts.hostname or "", parts.port
        unicode_host, ascii_host = host, host
        if host and ":" not in host:
            ascii_host = idna.encode(host, uts46=True).decode("ascii")
            unicode_host = idna.decode(ascii_host)
    except (ValueError, idna.IDNAError) as exc:
        raise ToolError("Invalid URL authority, port, or international hostname.") from exc
    try:
        if re.search(r"%(?![0-9A-Fa-f]{2})", parts.query):
            raise ValueError
        query = parse_qsl(parts.query, keep_blank_values=True, max_num_fields=1000, errors="strict")
    except (ValueError, UnicodeError) as exc:
        raise ToolError("Malformed query encoding or too many query fields.") from exc
    return {
        "original": source,
        "decoded_layers": decoded,
        "scheme": parts.scheme,
        "ascii_host": ascii_host,
        "unicode_host": unicode_host,
        "port": port,
        "path": parts.path,
        "query": [{"name": key, "value": item} for key, item in query],
        "fragment": parts.fragment,
        "has_userinfo": parts.username is not None,
        "absolute": bool(parts.scheme and parts.netloc),
    }


# Inspect bounded lines independently without visiting or resolving any supplied host.
def inspect_urls(options: UrlOptions) -> dict:
    lines = [line.strip() for line in options.text.splitlines() if line.strip()]
    if len(lines) > 200 or any(len(line) > 4096 for line in lines):
        raise ToolError("Use at most 200 URLs of 4,096 characters each.", "work_limit", 413)
    rows = []
    for line in lines:
        try:
            rows.append(inspect_one_url(line, options.decode_layers))
        except (ToolError, ValueError) as exc:
            rows.append(
                {
                    "original": line,
                    "error": exc.message
                    if isinstance(exc, ToolError)
                    else "Too many query fields.",
                }
            )
    return json_result(
        rows,
        {"urls": len(rows)},
        [
            "Offline parsing only; no URL was visited or hostname resolved. Parsing is not a safety verdict."
        ],
    )

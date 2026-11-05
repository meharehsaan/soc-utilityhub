import base64
import re
from datetime import UTC, datetime
from decimal import Decimal

from app.core.documents import DuplicateKey, load_document
from app.core.errors import ToolError
from app.schemas.jwt import JwtOptions
from app.utils import json_result


# Decode a canonical URL-safe segment without fetching keys or trusting its claims.
def decode_segment(segment: str) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", segment) or len(segment) % 4 == 1:
        raise ToolError("JWT segments must use unpadded Base64URL.")
    try:
        content = base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
        if base64.urlsafe_b64encode(content).decode().rstrip("=") != segment:
            raise ToolError("JWT segment has non-canonical padding bits.")
        value = load_document(content.decode("utf-8"))
    except (ValueError, UnicodeError, DuplicateKey) as exc:
        raise ToolError("JWT segment is not a unique-key UTF-8 JSON object.") from exc
    if not isinstance(value, dict):
        raise ToolError("JWT headers and claims must be JSON objects.")
    return value


# Display decoded JWT data with an explicit unverified status and bounded claim dates.
def inspect_jwt(options: JwtOptions) -> dict:
    token = options.text.strip()
    if len(token) > 200000:
        raise ToolError("JWT inspection is limited to 200,000 characters.", "work_limit", 413)
    pieces = token.split(".")
    if len(pieces) != 3:
        raise ToolError("Supply a three-segment signed JWT, not an encrypted JWE.")
    header, claims = decode_segment(pieces[0]), decode_segment(pieces[1])
    if pieces[2] and not re.fullmatch(r"[A-Za-z0-9_-]+", pieces[2]):
        raise ToolError("Signature segment must be Base64URL text.")
    times = {}
    for key in ("iat", "nbf", "exp"):
        if key in claims:
            value = claims[key]
            try:
                if type(value) not in {int, float, Decimal}:
                    raise ValueError
                times[key] = datetime.fromtimestamp(float(value), UTC).isoformat()
            except (ValueError, TypeError, OverflowError, OSError):
                times[key] = "Not a supported numeric calendar instant"
    return json_result(
        {
            "verification": "UNVERIFIED",
            "header": header,
            "claims": claims,
            "claim_times": times,
            "signature_present": bool(pieces[2]),
        },
        {"segments": 3},
        [
            "Decoding is not verification. Issuer, audience, signature, and claim validity have not been authenticated."
        ],
    )

from datetime import UTC, datetime, timedelta
from decimal import Decimal, DecimalException
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.errors import ToolError
from app.schemas.timestamp import TimestampOptions
from app.utils import json_result


# Resolve only an installed IANA timezone without consulting a remote service.
def timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ToolError("Choose a valid installed IANA timezone.") from exc


# Detect nonexistent and ambiguous local wall times instead of guessing an offset.
def localize(value: datetime, zone: ZoneInfo, ambiguity: str) -> datetime:
    choices = []
    for fold in (0, 1):
        candidate = value.replace(tzinfo=zone, fold=fold)
        if candidate.astimezone(UTC).astimezone(zone).replace(tzinfo=None) == value:
            if not any(item.utcoffset() == candidate.utcoffset() for item in choices):
                choices.append(candidate)
    if not choices:
        raise ToolError("Nonexistent local time during a timezone transition.")
    if len(choices) > 1:
        if ambiguity == "reject":
            raise ToolError("Ambiguous local time; explicitly choose the earlier or later instant.")
        choices.sort(key=datetime.timestamp)
        return choices[0 if ambiguity == "earlier" else -1]
    return choices[0]


# Convert one explicitly declared timestamp representation to an aware UTC datetime.
def parse_timestamp(
    value: str, format: str, input_zone: str = "UTC", ambiguity: str = "reject"
) -> datetime:
    if len(value) > 128:
        raise ToolError("Timestamp values are limited to 128 characters.")
    try:
        if format == "iso":
            result = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
            if result.tzinfo is None:
                result = localize(result, timezone(input_zone), ambiguity)
            return result.astimezone(UTC)
        number = Decimal(value.strip())
        if not number.is_finite():
            raise ToolError("Timestamp must be finite.")
        divisors = {
            "seconds": Decimal(1),
            "milliseconds": Decimal(1000),
            "microseconds": Decimal(1_000_000),
            "filetime": Decimal(10_000_000),
        }
        if format not in divisors:
            raise ToolError("Unsupported timestamp representation.")
        seconds = number / divisors[format]
        if format == "filetime":
            seconds -= Decimal(11644473600)
        if not Decimal(-62135596800) <= seconds <= Decimal(253402300799):
            raise ToolError("Timestamp is outside supported calendar years.")
        return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=int(seconds * 1_000_000))
    except (ValueError, OverflowError, DecimalException) as exc:
        raise ToolError("Invalid timestamp for the selected representation.") from exc


# Format epoch seconds exactly to microsecond precision without floating-point rounding.
def epoch_seconds(value: datetime) -> str:
    delta = value.astimezone(UTC) - datetime(1970, 1, 1, tzinfo=UTC)
    return str(
        Decimal(delta.days * 86400 + delta.seconds) + Decimal(delta.microseconds) / 1_000_000
    )


# Batch-convert explicit timestamps while retaining an error row for each invalid value.
def convert_timestamps(options: TimestampOptions) -> dict:
    zone = timezone(options.output_zone)
    lines = [line.strip() for line in options.text.splitlines() if line.strip()]
    if len(lines) > 1000:
        raise ToolError("Timestamp conversion is limited to 1,000 values.", "work_limit", 413)
    rows = []
    for line in lines:
        try:
            instant = parse_timestamp(line, options.format, options.input_zone, options.ambiguity)
            rows.append(
                {
                    "input": line,
                    "utc": instant.isoformat(),
                    "local": instant.astimezone(zone).isoformat(),
                    "zone": options.output_zone,
                    "unix_seconds": epoch_seconds(instant),
                }
            )
        except (ToolError, OverflowError) as exc:
            rows.append(
                {
                    "input": line,
                    "error": exc.message
                    if isinstance(exc, ToolError)
                    else "Output timezone exceeds supported calendar years.",
                }
            )
    return json_result(
        rows,
        {"values": len(rows), "errors": sum("error" in row for row in rows)},
        ["Precision is microseconds. Units and timezone assumptions are explicit."],
    )

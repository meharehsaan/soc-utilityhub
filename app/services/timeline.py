from decimal import Decimal

from app.core.errors import ToolError
from app.schemas.timeline import TimelineDocument, TimelineOptions
from app.services.timestamp import epoch_seconds, parse_timestamp
from app.utils import get_field, json_result, read_records


# Normalize explicit record timestamps while preserving provenance and unparsed evidence.
def build_timeline(options: TimelineOptions) -> dict:
    if options.documents and options.text:
        raise ToolError("Use pasted records or uploaded documents, not both.")
    documents = options.documents or [TimelineDocument(text=options.text)]
    if sum(len(document.text) for document in documents) > 1_000_000:
        raise ToolError(
            "Timeline inputs have a combined one-million-character limit.", "work_limit", 413
        )
    events, invalid = [], []
    for document in documents:
        for index, record in enumerate(read_records(document.text, options.format), 1):
            if len(events) + len(invalid) >= 5000:
                raise ToolError("Timeline supports 5,000 combined records.", "work_limit", 413)
            raw = get_field(record, options.time_field)
            try:
                if raw is None:
                    raise ToolError("Timestamp field is missing.")
                instant = parse_timestamp(
                    str(raw), options.timestamp_format, options.input_zone, options.ambiguity
                )
                events.append(
                    (
                        instant,
                        {
                            "source": document.label,
                            "record_index": index,
                            "original_timestamp": raw,
                            "utc": instant.isoformat(),
                            "host": get_field(record, options.host_field),
                            "user": get_field(record, options.user_field),
                            "action": get_field(record, options.action_field),
                        },
                    )
                )
            except ToolError as exc:
                invalid.append(
                    {
                        "source": document.label,
                        "record_index": index,
                        "error": exc.message,
                        "original_record": record,
                    }
                )
    events.sort(key=event_time)
    previous = None
    rows = []
    for instant, row in events:
        seconds = Decimal(epoch_seconds(instant))
        row["gap_seconds"] = None if previous is None else str(seconds - previous)
        previous = seconds
        rows.append(row)
    return json_result(
        {"events": rows, "unparsed": invalid},
        {"events": len(rows), "unparsed": len(invalid)},
        [
            "UTC ordering is stable. Record indexes count nonblank records; ambiguous or missing timestamps remain in unparsed evidence."
        ],
    )


# Compare aware instants without using display labels or input field order.
def event_time(event: tuple) -> object:
    return event[0]

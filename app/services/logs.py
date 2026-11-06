import csv
import io
import re
from collections import Counter
from typing import Any

from app.core.documents import DuplicateKey, dump_document, load_document
from app.core.errors import ToolError
from app.schemas.logs import LogsOptions
from app.utils import get_field

RECORD_LIMIT = 5000
SYSLOG = re.compile(
    r"^<(?P<priority>\d{1,3})>(?P<version>[1-9]\d{0,2}) (?P<timestamp>\S+) (?P<host>\S+) (?P<app>\S+) (?P<pid>\S+) (?P<msgid>\S+) (?P<body>.*)$"
)


# Parse RFC 5424 structured-data boundaries without splitting escaped closing brackets.
def parse_syslog(line: str) -> dict:
    match = SYSLOG.fullmatch(line)
    if not match or int(match["priority"]) > 191:
        raise ToolError("Not a supported RFC 5424 syslog record.")
    body = match["body"]
    if body.startswith("-"):
        if len(body) > 1 and body[1] != " ":
            raise ToolError("Invalid syslog structured-data boundary.")
        structured, message = "-", body[2:] if len(body) > 1 else ""
    elif body.startswith("["):
        position, escaped, quoted, end = 0, False, False, 0
        while position < len(body):
            char = body[position]
            if escaped:
                escaped = False
            elif char == "\\" and quoted:
                escaped = True
            elif char == '"':
                quoted = not quoted
            elif char == "]" and not quoted:
                end = position + 1
                if end == len(body) or body[end] != "[":
                    break
            position += 1
        if not end or quoted or (end < len(body) and body[end] != " "):
            raise ToolError("Invalid or unsupported syslog structured data.")
        structured, message = body[:end], body[end + 1 :]
    else:
        raise ToolError("Missing syslog structured data.")
    priority = int(match["priority"])
    return {
        "timestamp": match["timestamp"],
        "host": match["host"],
        "app": match["app"],
        "pid": match["pid"],
        "message_id": match["msgid"],
        "facility": priority // 8,
        "severity": priority % 8,
        "structured_data": structured,
        "message": message,
    }


# Retain each malformed line with a safe reason and its exact original content.
def line_records(text: str, format: str) -> list[dict]:
    lines = text.splitlines()
    if len(lines) > RECORD_LIMIT:
        raise ToolError("Logs are limited to 5,000 records.", "work_limit", 413)
    records = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = parse_syslog(line) if format == "syslog" else load_document(line)
            value = value if isinstance(value, dict) else {"value": value}
            records.append({"line": number, "value": value, "error": "", "raw": line})
        except (ToolError, DuplicateKey) as exc:
            if isinstance(exc, ToolError) and exc.status == 413:
                raise
            reason = exc.message if isinstance(exc, ToolError) else "Duplicate JSON keys."
            records.append({"line": number, "value": {}, "error": reason, "raw": line})
    return records


# Read CSV records with quoting and multiline boundaries while rejecting ambiguous headers.
def csv_records(text: str, delimiter: str) -> list[dict]:
    physical_lines = text.splitlines(keepends=True)
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
    try:
        headers = next(reader, [])
        if not headers or len(headers) > 64 or len(set(headers)) != len(headers):
            raise ToolError("CSV needs 1–64 unique column headers.")
        if any(not header or len(header) > 256 for header in headers):
            raise ToolError("CSV headers must contain 1–256 characters.")
        records = []
        previous_line = reader.line_num
        for row in reader:
            if len(records) >= RECORD_LIMIT:
                raise ToolError("CSV is limited to 5,000 records.", "work_limit", 413)
            line = previous_line + 1
            previous_line = reader.line_num
            if len(row) != len(headers):
                records.append(
                    {
                        "line": line,
                        "value": {},
                        "error": "Column count differs from the header.",
                        "raw": "".join(physical_lines[line - 1 : reader.line_num]),
                    }
                )
            else:
                records.append(
                    {
                        "line": line,
                        "value": dict(zip(headers, row, strict=True)),
                        "error": "",
                        "raw": "",
                    }
                )
        return records
    except csv.Error as exc:
        raise ToolError(
            "Malformed CSV quoting or a field exceeding the parser limit; original input is unchanged."
        ) from exc


# Convert cell values into exact inert strings without rounding nested JSON numbers.
def cell_text(value: Any) -> str:
    return value if isinstance(value, str) else dump_document(value, pretty=False)


# Escape spreadsheet formula prefixes without changing the underlying parsed records.
def spreadsheet_cell(value: str) -> str:
    if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")):
        return "'" + value
    return value


# Summarize explicitly selected network fields without inferring event safety.
def network_summary(records: list[dict], options: LogsOptions) -> dict:
    if options.network_preset == "none":
        return {}
    presets = {
        "zeek": ("id.orig_h", "id.resp_h", "id.resp_p", ["orig_bytes", "resp_bytes"]),
        "suricata": (
            "src_ip",
            "dest_ip",
            "dest_port",
            ["flow.bytes_toserver", "flow.bytes_toclient"],
        ),
        "custom": (
            options.source_field,
            options.destination_field,
            options.port_field,
            [options.bytes_field],
        ),
    }
    source, destination, port, byte_fields = presets[options.network_preset]
    result = {}
    for label, field in (
        ("sources", source),
        ("destinations", destination),
        ("destination_ports", port),
    ):
        values = [get_field(record["value"], field) for record in records]
        present = [cell_text(value) for value in values if value is not None]
        result[label] = {
            "field": field,
            "missing": len(records) - len(present),
            "top": Counter(present).most_common(10),
        }
    total, parsed, invalid = 0, 0, 0
    for record in records:
        for field in byte_fields:
            value = get_field(record["value"], field)
            if value is None:
                continue
            if (
                type(value) is int
                and 0 <= value <= 18446744073709551615
                or isinstance(value, str)
                and re.fullmatch(r"[0-9]{1,20}", value)
                and int(value) <= 18446744073709551615
            ):
                total += int(value)
                parsed += 1
            else:
                invalid += 1
    result["bytes"] = {
        "fields": byte_fields,
        "total": str(total),
        "numeric_values": parsed,
        "invalid_values": invalid,
    }
    result["records"] = len(records)
    return result


# Inspect records, choose a view, and export only explicitly selected transformations.
def inspect_logs(options: LogsOptions) -> dict:
    if options.format in {"csv", "tsv"}:
        records = csv_records(options.text, "," if options.format == "csv" else "\t")
    elif options.format == "json":
        try:
            document = load_document(options.text)
        except DuplicateKey as exc:
            raise ToolError(
                "Duplicate JSON keys detected; use raw inspection or resolve duplicates before tabulation."
            ) from exc
        values = document if isinstance(document, list) else [document]
        if len(values) > RECORD_LIMIT:
            raise ToolError("Logs are limited to 5,000 records.", "work_limit", 413)
        records = [
            {
                "line": i + 1,
                "value": item if isinstance(item, dict) else {"value": item},
                "error": "",
                "raw": "",
            }
            for i, item in enumerate(values)
        ]
    else:
        records = line_records(options.text, options.format)
    errors = [record for record in records if record["error"]]
    valid = [record for record in records if not record["error"]]
    columns = list(dict.fromkeys(key for record in valid for key in record["value"]))
    if len(columns) > 64 or any(len(key) > 256 for key in columns):
        raise ToolError(
            "Tabular inspection supports at most 64 columns with names up to 256 characters.",
            "work_limit",
            413,
        )
    if options.columns and any(column not in columns for column in options.columns):
        raise ToolError("A selected column does not exist in these records.")
    columns = list(dict.fromkeys(options.columns)) if options.columns else columns
    if options.filter_value:
        needle = options.filter_value.casefold()
        if options.filter_field and options.filter_field not in columns:
            raise ToolError("The filter field must be an available selected column.")
        valid = [
            record
            for record in valid
            if needle
            in (
                cell_text(record["value"].get(options.filter_field, ""))
                if options.filter_field
                else " ".join(cell_text(value) for value in record["value"].values())
            ).casefold()
        ]
    projected = [
        {key: record["value"][key] for key in columns if key in record["value"]} for record in valid
    ]
    network = network_summary(valid, options)
    if set(options.renames) - set(columns):
        raise ToolError("Rename keys must be selected source columns.")
    renamed_columns = [options.renames.get(column, column) for column in columns]
    if len(set(renamed_columns)) != len(renamed_columns):
        raise ToolError("Renaming would create duplicate column names.")
    summary = {}
    for column in columns:
        present = [record[column] for record in projected if column in record]
        summary[column] = {
            "missing": len(projected) - len(present),
            "top": Counter(cell_text(value) for value in present).most_common(10),
        }
    projected = [
        {options.renames.get(key, key): value for key, value in record.items()}
        for record in projected
    ]
    source_columns = columns
    columns = renamed_columns
    warnings = ["Column/filter choices affect exported records. Original input remains unchanged."]
    if errors:
        warnings.append(
            f"{len(errors)} malformed records retained in the error preview and JSON/JSONL exports."
        )
    if options.export == "csv":
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(
            [spreadsheet_cell(column) for column in columns]
            if options.spreadsheet_safe
            else columns
        )
        for record in projected:
            row = [cell_text(record.get(column, "")) for column in columns]
            writer.writerow(
                [spreadsheet_cell(value) for value in row] if options.spreadsheet_safe else row
            )
        output = buffer.getvalue()
        if errors:
            warnings.append(
                "CSV exports contain valid records only; choose JSON/JSONL to include error records."
            )
    else:
        exported = projected + [
            {"_source_line": record["line"], "_parse_error": record["error"], "_raw": record["raw"]}
            for record in errors
        ]
        output = (
            dump_document(exported)
            if options.export == "json"
            else "\n".join(dump_document(record, pretty=False) for record in exported)
        )
    rows = [
        [str(record["line"])]
        + [cell_text(record["value"].get(column, "")) for column in source_columns]
        for record in valid
    ]
    return {
        "output": output,
        "extension": "ndjson" if options.export == "jsonl" else options.export,
        "meta": {
            "source_records": len(records),
            "matching_records": len(valid),
            "malformed": len(errors),
        },
        "warnings": warnings,
        "data": {
            "columns": ["Source line"] + columns,
            "rows": rows,
            "errors": errors,
            "summary": summary,
            "network": network,
        },
    }

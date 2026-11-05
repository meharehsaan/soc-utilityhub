import re

from app.core.errors import ToolError
from app.schemas.strings import StringsOptions
from app.utils import json_result


# Extract printable runs with exact byte offsets while retaining invalid-byte boundaries.
def extract_strings(options: StringsOptions, content: bytes | None = None) -> dict:
    data = options.text.encode("utf-8") if content is None else content
    if len(data) > 5 * 1024 * 1024:
        raise ToolError("String extraction is limited to 5 MiB.", "work_limit", 413)
    rows, warnings = [], []
    if options.encoding == "ascii":
        for match in re.finditer(rb"[\x20-\x7e]+", data):
            if len(match.group()) >= options.minimum:
                rows.append(
                    {
                        "offset": match.start(),
                        "bytes": len(match.group()),
                        "text": match.group().decode("ascii"),
                    }
                )
            if len(rows) > 5000:
                raise ToolError(
                    "More than 5,000 strings; increase the minimum length.", "work_limit", 413
                )
    else:
        if options.encoding == "utf-16le":
            if len(data) % 2:
                warnings.append("A trailing incomplete UTF-16LE code unit was not decoded.")
            text = data[: len(data) // 2 * 2].decode("utf-16le", errors="surrogatepass")
        else:
            text = data.decode("utf-8", errors="surrogateescape")
        run, start, offset = [], 0, 0
        for character in text:
            width = len(
                character.encode(
                    options.encoding,
                    errors="surrogatepass" if options.encoding == "utf-16le" else "surrogateescape",
                )
            )
            if character.isprintable() or character == "\t":
                if not run:
                    start = offset
                run.append(character)
            else:
                if len(run) >= options.minimum:
                    rows.append({"offset": start, "bytes": offset - start, "text": "".join(run)})
                run = []
            offset += width
            if len(rows) > 5000:
                raise ToolError(
                    "More than 5,000 strings; increase the minimum length.", "work_limit", 413
                )
        if len(run) >= options.minimum:
            rows.append({"offset": start, "bytes": offset - start, "text": "".join(run)})
    if len(rows) > 5000:
        raise ToolError("More than 5,000 strings; increase the minimum length.", "work_limit", 413)
    return json_result(
        rows,
        {"strings": len(rows), "input_bytes": len(data), "encoding": options.encoding},
        warnings + ["Offsets are bytes. UTF-16LE scans alignment zero; no file was executed."],
    )

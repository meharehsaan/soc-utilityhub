import re

import regex

from app.core.errors import ToolError
from app.schemas.text import TextOptions


# Split text into explicit units while preserving a single terminal line separator.
def split_units(text: str, unit: str) -> tuple[list[str], bool]:
    if unit == "graphemes":
        try:
            return regex.findall(r"\X", text, timeout=1), False
        except TimeoutError as exc:
            raise ToolError(
                "Character segmentation exceeded its time limit.", "work_limit", 413
            ) from exc
    if unit == "words":
        return text.split(), False
    if not text:
        return [], False
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    final = normalized.endswith("\n")
    if final:
        normalized = normalized[:-1]
    return normalized.split("\n"), final


# Apply exactly one selected text action without silently chaining transformations.
def transform_text(options: TextOptions) -> dict:
    values, final = split_units(options.text, options.unit)
    original_count = len(values)
    if original_count > 100000:
        raise ToolError("Text operations are limited to 100,000 units.", "work_limit", 413)
    if options.action == "count":
        graphemes, _ = split_units(options.text, "graphemes")
        counts = {
            "characters": len(options.text),
            "graphemes": len(graphemes),
            "words": len(options.text.split()),
            "lines": len(split_units(options.text, "lines")[0]),
            "utf8_bytes": len(options.text.encode("utf-8")),
        }
        return {
            "output": "\n".join(f"{key}: {value}" for key, value in counts.items()),
            "meta": counts,
        }
    if options.action == "deduplicate":
        retained = []
        seen = set()
        indices = range(len(values) - 1, -1, -1) if options.keep == "last" else range(len(values))
        for index in indices:
            item = values[index]
            key = item.strip() if options.trim else item
            if options.remove_blank and not key.strip():
                continue
            if not options.case_sensitive:
                key = key.casefold()
            if key not in seen:
                retained.append(item)
                seen.add(key)
        values = list(reversed(retained)) if options.keep == "last" else retained
    else:
        if options.trim:
            values = [item.strip() for item in values]
        if options.remove_blank:
            values = [item for item in values if item.strip()]
        if options.action == "sort":
            # Build stable keys while avoiding integer conversion of huge numeric chunks.
            def key(item: str) -> str | list[tuple[int, str | tuple[int, str]]]:
                item = item if options.case_sensitive else item.casefold()
                if options.natural and options.unit != "graphemes":
                    return [
                        (1, (len(chunk.lstrip("0")), chunk.lstrip("0")))
                        if chunk.isdigit() and chunk.isascii()
                        else (0, chunk)
                        for chunk in re.split(r"([0-9]+)", item)
                    ]
                return item

            values = sorted(values, key=key, reverse=options.descending)
    separator = {"lines": "\n", "words": " ", "graphemes": ""}[options.unit]
    output = separator.join(values)
    if final and values:
        output += "\n"
    return {
        "output": output,
        "meta": {
            "input_units": original_count,
            "output_units": len(values),
            "removed": original_count - len(values),
        },
    }

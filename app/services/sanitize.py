import ipaddress
from collections import defaultdict
from typing import Any

import regex

from app.core.documents import DuplicateKey, dump_document, load_document
from app.core.errors import ToolError
from app.schemas.sanitize import Replacement, SanitizeOptions

PREFIXES = {
    "email": "EMAIL",
    "username": "USER",
    "company": "COMPANY",
    "domain": "DOMAIN",
    "hostname": "HOST",
    "ip": "IP",
    "custom": "VALUE",
}
MAX_MATCHES = 10000
EMAIL = r"(?<![\w.+-])[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?\.[A-Za-z]{2,63}(?![\w.-])"
IP = r"(?<![\w:.])[0-9A-Fa-f:.]{2,64}(?![\w:.])"


# Find only explicitly enabled built-in patterns and validate IP candidates.
def pattern_replacements(options: SanitizeOptions) -> list[Replacement]:
    entries = []
    seen = set()
    try:
        for kind in options.patterns:
            for match in regex.finditer(EMAIL if kind == "email" else IP, options.text, timeout=1):
                source = match.group()
                if kind == "ip":
                    try:
                        ipaddress.ip_address(source)
                    except ValueError:
                        continue
                if (kind, source) not in seen:
                    entries.append(Replacement(category=kind, source=source))
                    seen.add((kind, source))
                if len(entries) > 128:
                    raise ToolError(
                        "Pattern mode found more than 128 distinct values; narrow the input.",
                        "work_limit",
                        413,
                    )
    except TimeoutError as exc:
        raise ToolError("Pattern matching exceeded its time limit.", "work_limit", 413) from exc
    return entries


# Allocate predictable aliases that cannot collide with existing input placeholders.
def alias_value(category: str, text: str, counters: dict, blocked: set) -> str:
    prefix = PREFIXES[category]
    while counters[prefix] < 999:
        counters[prefix] += 1
        candidate = f"{prefix}_{counters[prefix]:03d}"
        if candidate not in blocked:
            blocked.add(candidate)
            return candidate
    raise ToolError("Input exhausts available alias names; supply custom replacements.")


# Mask selected exact JSON keys while preserving all other parsed values and precision.
def mask_fields(options: SanitizeOptions) -> dict:
    if not options.fields or any(not key or len(key) > 512 for key in options.fields):
        raise ToolError("Supply one or more exact JSON field names, up to 512 characters each.")
    try:
        document = load_document(options.text)
    except DuplicateKey as exc:
        raise ToolError("Duplicate JSON keys must be resolved before field masking.") from exc
    selected = set(options.fields)
    aliases, matches = {}, 0
    counters = defaultdict(int)
    blocked = set(regex.findall(r"(?:EMAIL|USER|COMPANY|DOMAIN|HOST|IP|VALUE)_\d{3}", options.text))

    # Replace matching field values using operation-local aliases, never a shared mapping.
    def walk(value: Any) -> Any:
        nonlocal matches
        if isinstance(value, list):
            return [walk(item) for item in value]
        if not isinstance(value, dict):
            return value
        result = {}
        for key, item in value.items():
            if key in selected:
                identity = dump_document(item, pretty=False)
                if identity not in aliases:
                    aliases[identity] = alias_value("custom", options.text, counters, blocked)
                result[key] = aliases[identity]
                matches += 1
            else:
                result[key] = walk(item)
        return result

    result = walk(document)
    return {
        "output": dump_document(result),
        "meta": {"masked_fields": matches, "unique_values": len(aliases)},
        "warnings": [
            "Selected fields were replaced; JSON formatting has been normalized. Review other fields before sharing."
        ],
    }


# Replace bounded literal matches once, choosing the longest source at each position.
def sanitize(options: SanitizeOptions) -> dict:
    if options.mode == "json_fields":
        return mask_fields(options)
    entries = options.replacements if options.mode == "literal" else pattern_replacements(options)
    if options.mode == "patterns" and not options.patterns:
        raise ToolError("Select at least one pattern type.")
    if options.mode == "literal" and not entries:
        raise ToolError("Supply at least one string to replace.")
    flags = 0 if options.case_sensitive else regex.IGNORECASE | regex.FULLCASE
    identities = set()
    for item in entries:
        identity = item.source if options.case_sensitive else item.source.casefold()
        if identity in identities:
            raise ToolError("A source string has multiple mappings; keep only one entry per value.")
        identities.add(identity)

    # Sort literal alternatives longest-first under the selected matching semantics.
    def source_length(item: Replacement) -> int:
        return len(item.source if options.case_sensitive else item.source.casefold())

    entries = sorted(entries, key=source_length, reverse=True)
    blocked = set(regex.findall(r"(?:EMAIL|USER|COMPANY|DOMAIN|HOST|IP|VALUE)_\d{3}", options.text))
    for item in entries:
        if item.replacement is not None:
            blocked.update(
                regex.findall(
                    r"(?:EMAIL|USER|COMPANY|DOMAIN|HOST|IP|VALUE)_\d{3}", item.replacement
                )
            )
    counters, counts = defaultdict(int), [0] * len(entries)
    replacements = [
        item.replacement
        if item.replacement is not None
        else alias_value(item.category, options.text, counters, blocked)
        for item in entries
    ]
    if not entries:
        return {
            "output": options.text,
            "meta": {"matches": 0, "distinct_values": 0},
            "warnings": ["No selected pattern matches were found."],
        }
    expression = "|".join(
        f"(?P<m{i}>{regex.escape(item.source)})" for i, item in enumerate(entries)
    )
    if options.whole_token:
        expression = rf"(?<!\w)(?:{expression})(?!\w)"
    pattern = regex.compile(expression, flags)
    chunks, spans, last, output_length, total = [], [], 0, 0, 0
    try:
        for match in pattern.finditer(options.text, timeout=1):
            total += 1
            if total > MAX_MATCHES:
                raise ToolError(
                    "More than 10,000 replacements; narrow the input.", "work_limit", 413
                )
            index = int(match.lastgroup[1:])
            before, replacement = options.text[last : match.start()], replacements[index]
            chunks.extend((before, replacement))
            output_length += len(before)
            spans.append([output_length, output_length + len(replacement)])
            output_length += len(replacement)
            counts[index] += 1
            last = match.end()
    except TimeoutError as exc:
        raise ToolError("Replacement matching exceeded its time limit.", "work_limit", 413) from exc
    chunks.append(options.text[last:])
    output = "".join(chunks)
    stats = [
        {"source": item.source, "replacement": replacements[i], "count": counts[i]}
        for i, item in enumerate(entries)
    ]
    return {
        "output": output,
        "meta": {"matches": total, "distinct_values": sum(count > 0 for count in counts)},
        "data": {"matches": stats, "spans": spans},
        "warnings": [
            "Only configured matches were replaced. Review the result for remaining sensitive information."
        ],
    }

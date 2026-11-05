import unicodedata

from app.core.errors import ToolError
from app.schemas.unicode import UnicodeOptions
from app.utils import json_result


# Reveal invisible/control characters without silently removing them.
def inspect_unicode(options: UnicodeOptions) -> dict:
    if options.action == "normalize":
        if len(options.text) > 200000:
            raise ToolError("Normalization is limited to 200,000 characters.", "work_limit", 413)
        output = unicodedata.normalize(options.form, options.text)
        return {
            "output": output,
            "meta": {"form": options.form, "changed": output != options.text},
            "warnings": ["Normalization can change identifiers. Original input remains unchanged."],
        }
    rows, count = [], 0
    for index, character in enumerate(options.text):
        category = unicodedata.category(character)
        suspicious = category in {"Cf", "Cc", "Zl", "Zp", "Mn", "Me"}
        if not options.include_whitespace and character in "\r\n\t":
            suspicious = False
        if suspicious:
            count += 1
            if len(rows) < 1000:
                rows.append(
                    {
                        "codepoint_offset": index,
                        "codepoint": f"U+{ord(character):04X}",
                        "name": unicodedata.name(character, "UNNAMED"),
                        "category": category,
                        "escaped": character.encode("unicode_escape").decode("ascii"),
                    }
                )
    return json_result(
        {
            "characters": rows,
            "normalization_changes": {
                form: unicodedata.normalize(form, options.text) != options.text
                for form in ("NFC", "NFD", "NFKC", "NFKD")
            },
        },
        {"suspicious_characters": count, "shown": len(rows)},
        [
            "Offsets are Unicode code points; at most 1,000 findings are displayed. No text was changed."
        ],
    )

import re
from pathlib import Path

import pytest

from app.catalog import TOOLS

CSS = Path("app/static/css/app.css").read_text()


# Read literal solid color tokens from one explicit theme or accent selector.
def tokens(selector: str) -> dict[str, str]:
    match = re.search(re.escape(selector) + r"\s*\{([^}]+)\}", CSS)
    assert match is not None
    return dict(re.findall(r"(--[\w-]+):\s*(#[0-9a-f]{6}|#[0-9a-f]{3})\b", match[1]))


# Compute standard relative luminance from either supported hexadecimal notation.
def luminance(color: str) -> float:
    value = color[1:]
    if len(value) == 3:
        value = "".join(character * 2 for character in value)
    channels = [int(value[index : index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        number / 12.92 if number <= 0.04045 else ((number + 0.055) / 1.055) ** 2.4
        for number in channels
    ]
    return sum(
        number * weight for number, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True)
    )


# Compare foreground and background colors using their standard luminance ratio.
def contrast(first: str, second: str) -> float:
    low, high = sorted((luminance(first), luminance(second)))
    return (high + 0.05) / (low + 0.05)


# Protect body text, service glyphs, and shared actions in both console themes.
@pytest.mark.parametrize("theme", ["dark", "light"])
def test_text_and_service_contrast(theme: str) -> None:
    root = ":root" if theme == "dark" else ":root[data-theme=light]"
    base = tokens(root)
    for foreground in ("--text", "--muted", "--subtle"):
        for background in ("--bg", "--surface", "--surface-raised", "--surface-hover", "--input"):
            assert contrast(base[foreground], base[background]) >= 4.5, (
                theme,
                foreground,
                background,
            )
    assert contrast(base["--primary-text"], base["--primary"]) >= 4.5
    assert contrast(base["--accent-text"], base["--accent"]) >= 4.5
    assert contrast(base["--gold-text"], base["--gold-bg"]) >= 4.5
    accents = set()
    for tool in TOOLS:
        selector = ("" if theme == "dark" else root + " ") + ".accent-" + tool.accent
        accent = tokens(selector)
        accents.add(accent["--tool-color"])
        assert contrast(accent["--tool-color"], accent["--tool-bg"]) >= 4.5, tool.slug
        assert contrast(accent["--tool-color"], base["--surface"]) >= 4.5, tool.slug
    assert len(accents) == len(TOOLS) == 32

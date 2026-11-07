from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from spellchecker import SpellChecker

import regex

from app.core.errors import ToolError
from app.schemas.spell import SpellOptions


# Load the fixed read-only English dictionary lazily without recording user vocabulary.
@lru_cache(maxsize=1)
def dictionary() -> "SpellChecker":
    try:
        from spellchecker import SpellChecker
    except ImportError as exc:
        raise ToolError(
            "Install pyspellchecker from requirements.txt.", "dependency_missing", 503
        ) from exc
    return SpellChecker(language="en", distance=1)


# Adapt a selected suggestion to simple source capitalization without changing punctuation.
def match_case(source: str, replacement: str) -> str:
    if source.isupper():
        return replacement.upper()
    if source.istitle():
        return replacement.capitalize()
    return replacement


# Suggest local spelling changes and apply only deliberate corrections or an explicit best-choice mode.
def check_spelling(options: SpellOptions) -> dict:
    if any(len(word) > 64 for word in options.ignore) or any(
        not key or len(key) > 64 or len(value) > 64 for key, value in options.corrections.items()
    ):
        raise ToolError("Ignore and correction entries must be at most 64 characters.")
    checker = dictionary()
    ignored = {word.casefold() for word in options.ignore}
    corrections = {word.casefold(): value for word, value in options.corrections.items()}
    suggestions, positions = {}, []
    try:
        for match in regex.finditer(r"[^\W\d_]+(?:['’][^\W\d_]+)*", options.text, timeout=1):
            word = match.group()
            key = word.casefold()
            if len(word) > 48 or key in ignored or (options.ignore_uppercase and word.isupper()):
                continue
            if key not in suggestions and key not in checker:
                if len(suggestions) >= 128:
                    raise ToolError(
                        "More than 128 unknown words; shorten the text or add ignore terms.",
                        "work_limit",
                        413,
                    )
                candidates = checker.candidates(key) or set()

                # Rank by the dictionary's fixed frequency with a deterministic tie break.
                def rank(candidate: str) -> tuple:
                    return (-checker[candidate], candidate)

                suggestions[key] = sorted(candidates, key=rank)[:5]
            positions.append((match.start(), match.end(), word, key))
    except TimeoutError as exc:
        raise ToolError(
            "Spelling tokenization exceeded its time limit.", "work_limit", 413
        ) from exc
    chunks, last, applied = [], 0, 0
    for start, end, word, key in positions:
        replacement = corrections.get(key)
        if replacement is None and options.apply_best and suggestions.get(key):
            replacement = suggestions[key][0]
        if replacement is not None:
            chunks.extend((options.text[last:start], match_case(word, replacement)))
            last = end
            applied += 1
    chunks.append(options.text[last:])
    return {
        "output": "".join(chunks),
        "meta": {"unknown_words": len(suggestions), "applied": applied},
        "data": {
            "suggestions": [
                {"word": key, "candidates": values} for key, values in suggestions.items()
            ]
        },
        "warnings": [
            "English spelling assistance, not grammar or factual verification. Acronyms and words longer than 48 characters are skipped by default; ignore lists are operation-local."
        ],
    }

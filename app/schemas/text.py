from typing import Literal

from app.schemas.common import TextRequest


class TextOptions(TextRequest):
    action: Literal["sort", "deduplicate", "cleanup", "count"] = "sort"
    unit: Literal["lines", "words", "graphemes"] = "lines"
    descending: bool = False
    natural: bool = False
    case_sensitive: bool = True
    trim: bool = False
    remove_blank: bool = False
    keep: Literal["first", "last"] = "first"

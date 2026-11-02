from typing import Literal

from pydantic import Field

from app.schemas.common import StrictModel, TextRequest


class Replacement(StrictModel):
    category: Literal["email", "username", "company", "domain", "hostname", "ip", "custom"]
    source: str = Field(min_length=1, max_length=512)
    replacement: str | None = Field(default=None, max_length=512)


class SanitizeOptions(TextRequest):
    mode: Literal["literal", "patterns", "json_fields"] = "literal"
    replacements: list[Replacement] = Field(default_factory=list, max_length=128)
    case_sensitive: bool = True
    whole_token: bool = False
    patterns: list[Literal["email", "ip"]] = Field(default_factory=list, max_length=2)
    fields: list[str] = Field(default_factory=list, max_length=64)

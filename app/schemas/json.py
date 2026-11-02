from typing import Literal

from pydantic import Field

from app.schemas.common import TextRequest


class JsonOptions(TextRequest):
    action: Literal["format", "minify", "query"] = "format"
    format: Literal["json", "jsonl"] = "json"
    record: int = Field(default=1, ge=1, le=5000)
    query: str = Field(default="", max_length=512)

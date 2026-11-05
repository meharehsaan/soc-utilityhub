from typing import Literal

from pydantic import Field

from app.schemas.common import TextRequest


class QueryOptions(TextRequest):
    table: str = Field(default="SecurityEvent", min_length=1, max_length=128)
    field: str = Field(default="Computer", min_length=1, max_length=128)
    operator: Literal["in", "in~", "has_any"] = "in"

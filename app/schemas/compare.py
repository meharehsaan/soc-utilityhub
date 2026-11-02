from typing import Literal

from pydantic import Field

from app.schemas.common import StrictModel


class CompareOptions(StrictModel):
    a: str = Field(max_length=1_000_000)
    b: str = Field(max_length=1_000_000)
    mode: Literal["lists", "text", "json"] = "lists"
    operation: Literal["a_only", "b_only", "intersection", "union"] = "a_only"
    trim: bool = False
    case_sensitive: bool = True
    ignore_key_order: bool = True

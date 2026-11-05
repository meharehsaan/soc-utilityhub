from pydantic import Field

from app.schemas.common import TextRequest


class SpellOptions(TextRequest):
    text: str = Field(max_length=20000)
    ignore: list[str] = Field(default_factory=list, max_length=128)
    corrections: dict[str, str] = Field(default_factory=dict, max_length=128)
    apply_best: bool = False
    ignore_uppercase: bool = True

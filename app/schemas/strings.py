from typing import Literal

from pydantic import Field

from app.schemas.common import TextRequest


class StringsOptions(TextRequest):
    encoding: Literal["ascii", "utf-8", "utf-16le"] = "ascii"
    minimum: int = Field(default=4, ge=1, le=256)

from typing import Literal

from pydantic import Field

from app.schemas.common import TextRequest


class IocOptions(TextRequest):
    mode: Literal["extract", "defang", "refang"] = "extract"
    types: list[Literal["ip", "domain", "url", "email", "hash"]] = Field(
        default=["ip", "domain", "url", "email", "hash"], max_length=5
    )

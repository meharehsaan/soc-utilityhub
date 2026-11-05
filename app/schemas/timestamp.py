from typing import Literal

from pydantic import Field

from app.schemas.common import TextRequest


class TimestampOptions(TextRequest):
    format: Literal["iso", "seconds", "milliseconds", "microseconds", "filetime"] = "iso"
    input_zone: str = Field(default="UTC", max_length=128)
    output_zone: str = Field(default="UTC", max_length=128)
    ambiguity: Literal["reject", "earlier", "later"] = "reject"

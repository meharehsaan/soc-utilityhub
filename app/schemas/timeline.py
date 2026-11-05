from typing import Literal

from pydantic import Field

from app.schemas.common import StrictModel, TextRequest


class TimelineDocument(StrictModel):
    label: str = Field(default="Pasted input", min_length=1, max_length=256)
    text: str = Field(max_length=1_000_000)


class TimelineOptions(TextRequest):
    documents: list[TimelineDocument] = Field(default_factory=list, max_length=4)
    format: Literal["json", "jsonl"] = "jsonl"
    time_field: str = Field(default="timestamp", min_length=1, max_length=128)
    timestamp_format: Literal["iso", "seconds", "milliseconds", "microseconds", "filetime"] = "iso"
    input_zone: str = Field(default="UTC", max_length=128)
    ambiguity: Literal["reject", "earlier", "later"] = "reject"
    host_field: str = Field(default="host", max_length=128)
    user_field: str = Field(default="user", max_length=128)
    action_field: str = Field(default="action", max_length=128)

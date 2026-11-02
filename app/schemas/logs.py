from typing import Literal

from pydantic import Field

from app.schemas.common import TextRequest


class LogsOptions(TextRequest):
    format: Literal["jsonl", "json", "csv", "tsv", "syslog"] = "jsonl"
    export: Literal["jsonl", "json", "csv"] = "jsonl"
    columns: list[str] = Field(default_factory=list, max_length=64)
    filter_field: str = Field(default="", max_length=256)
    filter_value: str = Field(default="", max_length=512)
    spreadsheet_safe: bool = True

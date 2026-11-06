from typing import Annotated, Literal

from pydantic import Field

from app.schemas.common import TextRequest


class LogsOptions(TextRequest):
    format: Literal["jsonl", "json", "csv", "tsv", "syslog"] = "jsonl"
    export: Literal["jsonl", "json", "csv"] = "jsonl"
    columns: list[str] = Field(default_factory=list, max_length=64)
    filter_field: str = Field(default="", max_length=256)
    filter_value: str = Field(default="", max_length=512)
    spreadsheet_safe: bool = True
    renames: dict[
        Annotated[str, Field(min_length=1, max_length=256)],
        Annotated[str, Field(min_length=1, max_length=256)],
    ] = Field(default_factory=dict, max_length=64)
    network_preset: Literal["none", "custom", "zeek", "suricata"] = "none"
    source_field: str = Field(default="src_ip", max_length=128)
    destination_field: str = Field(default="dest_ip", max_length=128)
    port_field: str = Field(default="dest_port", max_length=128)
    bytes_field: str = Field(default="bytes", max_length=128)

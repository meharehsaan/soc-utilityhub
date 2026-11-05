from typing import Literal

from pydantic import Field

from app.schemas.common import TextRequest


class ProcessTreeOptions(TextRequest):
    format: Literal["json", "jsonl"] = "jsonl"
    export: Literal["tree", "json"] = "tree"
    guid_field: str = Field(default="ProcessGuid", max_length=128)
    parent_field: str = Field(default="ParentProcessGuid", max_length=128)
    host_field: str = Field(default="Computer", max_length=128)
    image_field: str = Field(default="Image", max_length=128)
    command_field: str = Field(default="CommandLine", max_length=128)
    pid_field: str = Field(default="ProcessId", max_length=128)

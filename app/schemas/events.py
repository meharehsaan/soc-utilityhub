from typing import Literal

from pydantic import Field

from app.schemas.common import TextRequest


class EventsOptions(TextRequest):
    mode: Literal["parse", "lookup"] = "parse"
    format: Literal["xml", "json"] = "xml"
    provider: Literal["Microsoft-Windows-Security-Auditing", "Microsoft-Windows-Sysmon"] = (
        "Microsoft-Windows-Security-Auditing"
    )
    event_id: int = Field(default=4624, ge=0, le=65535)

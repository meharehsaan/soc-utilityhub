from pydantic import Field

from app.schemas.common import TextRequest


class ReportOptions(TextRequest):
    title: str = Field(default="Investigation handover", min_length=1, max_length=200)
    timeline: str = Field(default="", max_length=100000)
    indicators: str = Field(default="", max_length=100000)
    actions: str = Field(default="", max_length=100000)
    gaps: str = Field(default="", max_length=100000)
    next_steps: str = Field(default="", max_length=100000)

from pydantic import Field

from app.schemas.common import TextRequest


class UrlOptions(TextRequest):
    decode_layers: int = Field(default=0, ge=0, le=3)

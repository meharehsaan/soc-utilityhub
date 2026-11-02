from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    # Reject lone surrogate code points before UTF-8 serialization or hashing.
    @model_validator(mode="after")
    def valid_unicode(self) -> Self:
        pending = [self.model_dump()]
        while pending:
            value = pending.pop()
            if isinstance(value, str):
                try:
                    value.encode("utf-8")
                except UnicodeEncodeError as exc:
                    raise ValueError("Text contains an invalid Unicode surrogate.") from exc
            elif isinstance(value, dict):
                pending.extend(value.keys())
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
        return self


class TextRequest(StrictModel):
    text: str = Field(max_length=1_000_000)

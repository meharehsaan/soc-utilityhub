from typing import Literal

from app.schemas.common import TextRequest


class UnicodeOptions(TextRequest):
    action: Literal["inspect", "normalize"] = "inspect"
    form: Literal["NFC", "NFD", "NFKC", "NFKD"] = "NFC"
    include_whitespace: bool = False

from typing import Literal

from app.schemas.common import TextRequest


class StixOptions(TextRequest):
    mode: Literal["inspect", "export"] = "inspect"
    observable: Literal[
        "ipv4-addr", "ipv6-addr", "domain-name", "url", "email-addr", "file-sha256"
    ] = "ipv4-addr"

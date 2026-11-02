from typing import Literal

from pydantic import Field

from app.schemas.common import TextRequest

ALGORITHMS = (
    "md5",
    "sha1",
    "sha224",
    "sha256",
    "sha384",
    "sha512",
    "sha3_224",
    "sha3_256",
    "sha3_384",
    "sha3_512",
    "blake2b",
    "blake2s",
)


# Return independent default digest selections for each request.
def default_algorithms() -> list[str]:
    return ["md5", "sha1", "sha256"]


class HashOptions(TextRequest):
    action: Literal["hash", "identify"] = "hash"
    algorithms: list[str] = Field(default_factory=default_algorithms, max_length=12)
    expected: str = Field(default="", max_length=128)

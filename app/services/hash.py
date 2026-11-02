import hashlib
import re
from pathlib import PurePosixPath
from typing import BinaryIO

from app.core.errors import ToolError
from app.schemas.hash import ALGORITHMS, HashOptions

SIGNATURES = (
    (b"%PDF-", "PDF", {".pdf"}),
    (b"\x89PNG\r\n\x1a\n", "PNG", {".png"}),
    (b"\xff\xd8\xff", "JPEG", {".jpg", ".jpeg"}),
    (b"GIF87a", "GIF", {".gif"}),
    (b"GIF89a", "GIF", {".gif"}),
    (b"PK\x03\x04", "ZIP container", {".zip", ".docx", ".xlsx", ".pptx", ".jar"}),
    (b"\x7fELF", "ELF header", {".elf", ".so", ""}),
    (b"MZ", "DOS/PE header", {".exe", ".dll", ".sys", ".scr"}),
    (b"\x1f\x8b", "GZIP", {".gz", ".tgz"}),
)


# Validate a bounded explicit algorithm list before constructing any digest objects.
def selected_algorithms(names: list[str]) -> list[str]:
    if not names or len(names) > 12 or any(name not in ALGORITHMS for name in names):
        raise ToolError("Choose one or more supported hash algorithms.")
    return list(dict.fromkeys(names))


# Describe a candidate hexadecimal representation without claiming a definitive algorithm.
def identify_hash(value: str) -> dict:
    candidate = value.strip()
    if not candidate or not re.fullmatch(r"[0-9a-fA-F]+", candidate):
        raise ToolError("A candidate hash must contain hexadecimal characters only.")
    candidates = {
        32: "MD5 or another 128-bit format (including NTLM)",
        40: "SHA-1 or another 160-bit format",
        56: "SHA-224 / SHA3-224",
        64: "SHA-256 / SHA3-256 / BLAKE2s",
        96: "SHA-384 / SHA3-384",
        128: "SHA-512 / SHA3-512 / BLAKE2b",
    }
    result = candidates.get(len(candidate), "Unrecognized digest length")
    return {
        "output": result,
        "meta": {"hex_characters": len(candidate), "bits": len(candidate) * 4},
        "warnings": [
            "Length and syntax identify candidates only; they cannot prove an algorithm or benignness."
        ],
    }


# Extract bounded magic-signature observations without parsing or executing the file.
def file_metadata(prefix: bytes, filename: str = "") -> dict:
    extension = PurePosixPath(filename.replace("\\", "/")).suffix.lower()
    for magic, kind, expected in SIGNATURES:
        if prefix.startswith(magic):
            return {
                "signature": kind,
                "extension_mismatch": bool(filename and extension not in expected),
            }
    return {"signature": "Unknown / no supported signature", "extension_mismatch": False}


# Format selected digests and an optional expected-value comparison for safe export.
def digest_result(
    digests: dict, size: int, prefix: bytes, expected: str = "", filename: str = ""
) -> dict:
    if expected and not re.fullmatch(r"[0-9A-Fa-f]{1,128}", expected):
        raise ToolError("Expected digest must be hexadecimal without spaces.")
    values = {name: digest.hexdigest() for name, digest in digests.items()}
    meta = {"bytes": size, **file_metadata(prefix, filename)}
    if expected:
        meta["expected_match"] = any(value == expected.lower() for value in values.values())
    return {
        "output": "\n".join(f"{name.upper()}: {value}" for name, value in values.items()),
        "meta": meta,
        "data": {"digests": values},
        "warnings": [
            "MD5/SHA-1 are legacy fingerprints. File signatures and matching digests are not safety verdicts."
        ],
    }


# Construct only supported fingerprint primitives, reporting unavailable algorithms clearly.
def make_digests(names: list[str]) -> dict:
    try:
        return {
            name: hashlib.new(name, usedforsecurity=False) for name in selected_algorithms(names)
        }
    except ValueError as exc:
        raise ToolError("A selected algorithm is unavailable in this Python build.") from exc


# Hash a file stream once while bounding bytes independently of upload metadata.
def hash_stream(stream: BinaryIO, names: list[str], expected: str = "", filename: str = "") -> dict:
    digests, size, prefix = make_digests(names), 0, b""
    while chunk := stream.read(65536):
        size += len(chunk)
        if size > 50 * 1024 * 1024:
            raise ToolError("Server hash files must be 50 MiB or smaller.", "input_too_large", 413)
        if not prefix:
            prefix = chunk[:32]
        for digest in digests.values():
            digest.update(chunk)
    return digest_result(digests, size, prefix, expected, filename)


# Hash exact text bytes or identify an explicitly selected candidate format.
def hash_text(options: HashOptions) -> dict:
    if options.action == "identify":
        return identify_hash(options.text)
    content = options.text.encode("utf-8")
    digests = make_digests(options.algorithms)
    for digest in digests.values():
        digest.update(content)
    return digest_result(digests, len(content), content[:32], options.expected)

from fastapi import UploadFile

from app.core.errors import ToolError

ENCODINGS = {"utf-8": "utf-8-sig", "windows-1252": "cp1252", "latin-1": "latin-1"}


# Read bounded inert bytes and release the upload on every completion path.
async def read_upload(file: UploadFile, limit: int = 5 * 1024 * 1024) -> bytes:
    chunks, size = [], 0
    try:
        while chunk := await file.read(65536):
            size += len(chunk)
            if size > limit:
                raise ToolError("File exceeds this tool's upload limit.", "input_too_large", 413)
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        await file.close()


# Decode only an explicitly selected encoding and retain all whitespace.
def decode_text(content: bytes, encoding: str = "utf-8") -> str:
    if encoding not in ENCODINGS:
        raise ToolError("Choose UTF-8, Windows-1252, or Latin-1.")
    try:
        text = content.decode(ENCODINGS[encoding], errors="strict")
    except UnicodeDecodeError as exc:
        raise ToolError(
            "File cannot be decoded using the selected encoding.", "invalid_encoding"
        ) from exc
    if len(text) > 1_000_000:
        raise ToolError("Text exceeds one million characters.", "input_too_large", 413)
    return text

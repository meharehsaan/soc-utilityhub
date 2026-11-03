import json
from contextlib import asynccontextmanager

from fastapi import Request
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from app.core.documents import DuplicateKey, unique_object
from app.core.errors import ToolError


# Validate one bounded upload form instead of accepting an unlimited multipart collection.
@asynccontextmanager
async def upload_form(request: Request, *, hash_file: bool = False):
    allowed = {"file", "algorithms", "expected"} if hash_file else {"file", "options", "encoding"}
    async with request.form(max_files=1, max_fields=3, max_part_size=131072) as form:
        if set(form.keys()) - allowed or any(len(form.getlist(key)) != 1 for key in form):
            raise ToolError("Unexpected or repeated upload fields.")
        file = form.get("file")
        if not isinstance(file, UploadFile):
            raise ToolError("Supply exactly one uploaded file.")
        yield file, form


# Validate file options using the same schema as pasted content without allowing two sources.
def file_options(model, options: str, text: str):
    if len(options) > 131072:
        raise ToolError("Upload options are too large.", "input_too_large", 413)
    try:
        values = json.loads(options, object_pairs_hook=unique_object)
    except (ValueError, DuplicateKey) as exc:
        raise ToolError("Upload options must be valid JSON with unique keys.") from exc
    if not isinstance(values, dict) or "text" in values:
        raise ToolError("Use the file as the sole text source.")
    try:
        return model.model_validate({**values, "text": text})
    except ValidationError as exc:
        raise ToolError("Check the uploaded file's options.", "invalid_options", 422) from exc

import json

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from app.core.documents import respond
from app.core.errors import ToolError
from app.routers.helpers import upload_form
from app.schemas.hash import HashOptions
from app.services.hash import hash_stream, hash_text, selected_algorithms
from app.web import tool_page

router = APIRouter()


# Render explicit browser/server hashing controls.
@router.get("/hash")
def page(request: Request) -> Response:
    return tool_page(request, "hash")


# Hash exact submitted text without trimming, newline conversion, or normalization.
@router.post("/api/v1/hash")
def run(payload: HashOptions) -> Response:
    return respond(hash_text(payload))


# Stream one inert uploaded file through all selected algorithms and close it on exit.
@router.post("/api/v1/hash/file")
async def run_file(request: Request) -> Response:
    async with upload_form(request, hash_file=True) as (file, form):
        try:
            names = json.loads(str(form.get("algorithms", '["md5","sha1","sha256"]')))
        except ValueError as exc:
            raise ToolError("Algorithms must be a JSON list.") from exc
        if not isinstance(names, list):
            raise ToolError("Algorithms must be a JSON list.")
        selected_algorithms(names)
        expected = str(form.get("expected", ""))
        if len(expected) > 128:
            raise ToolError("Expected digest is too long.")
        result = await run_in_threadpool(
            hash_stream, file.file, names, expected, file.filename or ""
        )
        return respond(result)

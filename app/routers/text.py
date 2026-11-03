from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from app.core.documents import respond
from app.core.uploads import decode_text, read_upload
from app.routers.helpers import file_options, upload_form
from app.schemas.text import TextOptions
from app.services.text import transform_text
from app.web import tool_page

router = APIRouter()


# Render the dedicated text workspace without starting transformation work.
@router.get("/text")
def page(request: Request):
    return tool_page(request, "text")


# Process typed pasted content on the bounded application worker pool.
@router.post("/api/v1/text")
def run(payload: TextOptions):
    return respond(transform_text(payload))


# Decode one explicitly selected upload and reuse the same validated transformation.
@router.post("/api/v1/text/file")
async def run_file(request: Request):
    async with upload_form(request) as (file, form):
        content = await read_upload(file)
        text = decode_text(content, str(form.get("encoding", "utf-8")))
        payload = file_options(TextOptions, str(form.get("options", "{}")), text)
        result = await run_in_threadpool(transform_text, payload)
        return respond(result)

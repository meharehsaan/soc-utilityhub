from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from app.core.documents import respond
from app.core.uploads import decode_text, read_upload
from app.routers.helpers import file_options, upload_form
from app.schemas.stix import StixOptions
from app.services.stix import inspect_stix
from app.web import tool_page

router = APIRouter()


# Render the dedicated stix controls without evaluating input.
@router.get("/stix")
def page(request: Request):
    return tool_page(request, "stix")


# Validate options before running this tool on the bounded worker pool.
@router.post("/api/v1/stix")
def run(payload: StixOptions):
    return respond(inspect_stix(payload))


# Read one inert upload and reuse the same request schema and transformation.
@router.post("/api/v1/stix/file")
async def run_file(request: Request):
    async with upload_form(request) as (file, form):
        content = await read_upload(file)
        text = decode_text(content, str(form.get("encoding", "utf-8")))
        payload = file_options(StixOptions, str(form.get("options", "{}")), text)
        return respond(await run_in_threadpool(inspect_stix, payload))

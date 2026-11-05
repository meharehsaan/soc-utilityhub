from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from app.core.documents import respond
from app.core.uploads import read_upload
from app.routers.helpers import file_options, upload_form
from app.schemas.strings import StringsOptions
from app.services.strings import extract_strings
from app.web import tool_page

router = APIRouter()


# Render the dedicated strings controls without evaluating input.
@router.get("/strings")
def page(request: Request):
    return tool_page(request, "strings")


# Validate options before running this tool on the bounded worker pool.
@router.post("/api/v1/strings")
def run(payload: StringsOptions):
    return respond(extract_strings(payload))


# Read one inert upload and reuse the same request schema and transformation.
@router.post("/api/v1/strings/file")
async def run_file(request: Request):
    async with upload_form(request) as (file, form):
        content = await read_upload(file)
        payload = file_options(StringsOptions, str(form.get("options", "{}")), "")
        return respond(await run_in_threadpool(extract_strings, payload, content))

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from app.core.documents import respond
from app.core.uploads import decode_text, read_upload
from app.routers.helpers import file_options, upload_form
from app.schemas.sigma import SigmaOptions
from app.services.sigma import inspect_sigma
from app.web import tool_page

router = APIRouter()


# Render the dedicated sigma controls without evaluating input.
@router.get("/sigma")
def page(request: Request) -> Response:
    return tool_page(request, "sigma")


# Validate options before running this tool on the bounded worker pool.
@router.post("/api/v1/sigma")
def run(payload: SigmaOptions) -> Response:
    return respond(inspect_sigma(payload))


# Read one inert upload and reuse the same request schema and transformation.
@router.post("/api/v1/sigma/file")
async def run_file(request: Request) -> Response:
    async with upload_form(request) as (file, form):
        content = await read_upload(file)
        text = decode_text(content, str(form.get("encoding", "utf-8")))
        payload = file_options(SigmaOptions, str(form.get("options", "{}")), text)
        return respond(await run_in_threadpool(inspect_sigma, payload))

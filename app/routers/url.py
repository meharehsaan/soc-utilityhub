from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from app.core.documents import respond
from app.core.uploads import decode_text, read_upload
from app.routers.helpers import file_options, upload_form
from app.schemas.url import UrlOptions
from app.services.url import inspect_urls
from app.web import tool_page

router = APIRouter()


# Render the dedicated url controls without evaluating input.
@router.get("/url")
def page(request: Request) -> Response:
    return tool_page(request, "url")


# Validate options before running this tool on the bounded worker pool.
@router.post("/api/v1/url")
def run(payload: UrlOptions) -> Response:
    return respond(inspect_urls(payload))


# Read one inert upload and reuse the same request schema and transformation.
@router.post("/api/v1/url/file")
async def run_file(request: Request) -> Response:
    async with upload_form(request) as (file, form):
        content = await read_upload(file)
        text = decode_text(content, str(form.get("encoding", "utf-8")))
        payload = file_options(UrlOptions, str(form.get("options", "{}")), text)
        return respond(await run_in_threadpool(inspect_urls, payload))

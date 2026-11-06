from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from app.core.documents import respond
from app.core.uploads import decode_text, read_upload
from app.routers.helpers import file_options, upload_form
from app.schemas.timeline import TimelineOptions
from app.services.timeline import build_timeline
from app.web import tool_page

router = APIRouter()


# Render the dedicated timeline controls without evaluating input.
@router.get("/timeline")
def page(request: Request) -> Response:
    return tool_page(request, "timeline")


# Validate options before running this tool on the bounded worker pool.
@router.post("/api/v1/timeline")
def run(payload: TimelineOptions) -> Response:
    return respond(build_timeline(payload))


# Read one inert upload and reuse the same request schema and transformation.
@router.post("/api/v1/timeline/file")
async def run_file(request: Request) -> Response:
    async with upload_form(request) as (file, form):
        content = await read_upload(file)
        text = decode_text(content, str(form.get("encoding", "utf-8")))
        payload = file_options(TimelineOptions, str(form.get("options", "{}")), text)
        return respond(await run_in_threadpool(build_timeline, payload))

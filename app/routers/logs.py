from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from app.core.documents import respond
from app.core.uploads import decode_text, read_upload
from app.routers.helpers import file_options, upload_form
from app.schemas.logs import LogsOptions
from app.services.logs import inspect_logs
from app.web import tool_page

router = APIRouter()


# Render the dedicated logs workspace without starting transformation work.
@router.get("/logs")
def page(request: Request) -> Response:
    return tool_page(request, "logs")


# Process typed pasted content on the bounded application worker pool.
@router.post("/api/v1/logs")
def run(payload: LogsOptions) -> Response:
    return respond(inspect_logs(payload))


# Decode one explicitly selected upload and reuse the same validated transformation.
@router.post("/api/v1/logs/file")
async def run_file(request: Request) -> Response:
    async with upload_form(request) as (file, form):
        content = await read_upload(file)
        text = decode_text(content, str(form.get("encoding", "utf-8")))
        payload = file_options(LogsOptions, str(form.get("options", "{}")), text)
        result = await run_in_threadpool(inspect_logs, payload)
        return respond(result)

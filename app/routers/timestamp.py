from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from app.core.documents import respond
from app.core.uploads import decode_text, read_upload
from app.routers.helpers import file_options, upload_form
from app.schemas.timestamp import TimestampOptions
from app.services.timestamp import convert_timestamps
from app.web import tool_page

router = APIRouter()


# Render the dedicated timestamp controls without evaluating input.
@router.get("/timestamp")
def page(request: Request):
    return tool_page(request, "timestamp")


# Validate options before running this tool on the bounded worker pool.
@router.post("/api/v1/timestamp")
def run(payload: TimestampOptions):
    return respond(convert_timestamps(payload))


# Read one inert upload and reuse the same request schema and transformation.
@router.post("/api/v1/timestamp/file")
async def run_file(request: Request):
    async with upload_form(request) as (file, form):
        content = await read_upload(file)
        text = decode_text(content, str(form.get("encoding", "utf-8")))
        payload = file_options(TimestampOptions, str(form.get("options", "{}")), text)
        return respond(await run_in_threadpool(convert_timestamps, payload))

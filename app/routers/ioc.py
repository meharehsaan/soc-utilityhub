from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from app.core.documents import respond
from app.core.uploads import decode_text, read_upload
from app.routers.helpers import file_options, upload_form
from app.schemas.ioc import IocOptions
from app.services.ioc import inspect_iocs
from app.web import tool_page

router = APIRouter()


# Render the dedicated ioc controls without evaluating input.
@router.get("/ioc")
def page(request: Request) -> Response:
    return tool_page(request, "ioc")


# Validate options before running this tool on the bounded worker pool.
@router.post("/api/v1/ioc")
def run(payload: IocOptions) -> Response:
    return respond(inspect_iocs(payload))


# Read one inert upload and reuse the same request schema and transformation.
@router.post("/api/v1/ioc/file")
async def run_file(request: Request) -> Response:
    async with upload_form(request) as (file, form):
        content = await read_upload(file)
        text = decode_text(content, str(form.get("encoding", "utf-8")))
        payload = file_options(IocOptions, str(form.get("options", "{}")), text)
        return respond(await run_in_threadpool(inspect_iocs, payload))

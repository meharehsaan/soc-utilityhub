from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from app.core.documents import respond
from app.core.uploads import decode_text, read_upload
from app.routers.helpers import file_options, upload_form
from app.schemas.process_tree import ProcessTreeOptions
from app.services.process_tree import build_process_tree
from app.web import tool_page

router = APIRouter()


# Render the dedicated process-tree controls without evaluating input.
@router.get("/process-tree")
def page(request: Request):
    return tool_page(request, "process-tree")


# Validate options before running this tool on the bounded worker pool.
@router.post("/api/v1/process-tree")
def run(payload: ProcessTreeOptions):
    return respond(build_process_tree(payload))


# Read one inert upload and reuse the same request schema and transformation.
@router.post("/api/v1/process-tree/file")
async def run_file(request: Request):
    async with upload_form(request) as (file, form):
        content = await read_upload(file)
        text = decode_text(content, str(form.get("encoding", "utf-8")))
        payload = file_options(ProcessTreeOptions, str(form.get("options", "{}")), text)
        return respond(await run_in_threadpool(build_process_tree, payload))

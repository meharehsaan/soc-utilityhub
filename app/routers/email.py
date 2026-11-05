from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from app.core.documents import respond
from app.core.uploads import read_upload
from app.routers.helpers import file_options, upload_form
from app.schemas.email import EmailOptions
from app.services.email import inspect_email
from app.web import tool_page

router = APIRouter()


# Render the dedicated email controls without evaluating input.
@router.get("/email")
def page(request: Request):
    return tool_page(request, "email")


# Validate options before running this tool on the bounded worker pool.
@router.post("/api/v1/email")
def run(payload: EmailOptions):
    return respond(inspect_email(payload))


# Read one inert upload and reuse the same request schema and transformation.
@router.post("/api/v1/email/file")
async def run_file(request: Request):
    async with upload_form(request) as (file, form):
        content = await read_upload(file)
        payload = file_options(EmailOptions, str(form.get("options", "{}")), "")
        return respond(await run_in_threadpool(inspect_email, payload, content))

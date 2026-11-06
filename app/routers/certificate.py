from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from app.core.documents import respond
from app.core.uploads import read_upload
from app.routers.helpers import file_options, upload_form
from app.schemas.certificate import CertificateOptions
from app.services.certificate import inspect_certificates
from app.web import tool_page

router = APIRouter()


# Render the dedicated certificate controls without evaluating input.
@router.get("/certificate")
def page(request: Request) -> Response:
    return tool_page(request, "certificate")


# Validate options before running this tool on the bounded worker pool.
@router.post("/api/v1/certificate")
def run(payload: CertificateOptions) -> Response:
    return respond(inspect_certificates(payload))


# Read one inert upload and reuse the same request schema and transformation.
@router.post("/api/v1/certificate/file")
async def run_file(request: Request) -> Response:
    async with upload_form(request) as (file, form):
        content = await read_upload(file)
        payload = file_options(CertificateOptions, str(form.get("options", "{}")), "")
        return respond(await run_in_threadpool(inspect_certificates, payload, content))

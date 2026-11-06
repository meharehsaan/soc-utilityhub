from fastapi import APIRouter, Request
from starlette.responses import Response

from app.web import tool_page

router = APIRouter()


# Serve local signature controls without accepting signature uploads.
@router.get("/signature")
def page(request: Request) -> Response:
    return tool_page(request, "signature")

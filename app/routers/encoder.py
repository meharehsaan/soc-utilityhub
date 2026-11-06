from fastapi import APIRouter, Request
from starlette.responses import Response

from app.web import tool_page

router = APIRouter()


# Serve browser-only encoding controls without accepting transformation uploads.
@router.get("/encoder")
def page(request: Request) -> Response:
    return tool_page(request, "encoder")

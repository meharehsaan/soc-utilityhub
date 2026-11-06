from fastapi import APIRouter, Request
from starlette.responses import Response

from app.web import tool_page

router = APIRouter()


# Serve dedicated browser controls without accepting transformation uploads.
@router.get("/user-sid")
def page(request: Request) -> Response:
    return tool_page(request, "user-sid")

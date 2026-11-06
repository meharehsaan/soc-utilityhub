from fastapi import APIRouter, Request

from app.web import tool_page

router = APIRouter()


# Serve dedicated browser controls without accepting transformation uploads.
@router.get("/entropy")
def page(request: Request):
    return tool_page(request, "entropy")

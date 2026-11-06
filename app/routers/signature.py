from fastapi import APIRouter, Request

from app.web import tool_page

router = APIRouter()


# Serve local signature controls without accepting signature uploads.
@router.get("/signature")
def page(request: Request):
    return tool_page(request, "signature")

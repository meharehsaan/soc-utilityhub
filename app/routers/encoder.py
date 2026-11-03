from fastapi import APIRouter, Request

from app.web import tool_page

router = APIRouter()


# Serve browser-only encoding controls without accepting transformation uploads.
@router.get("/encoder")
def page(request: Request):
    return tool_page(request, "encoder")

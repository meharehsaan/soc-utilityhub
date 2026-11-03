from fastapi import APIRouter, Request

from app.core.documents import respond
from app.schemas.compare import CompareOptions
from app.services.compare import compare
from app.web import tool_page

router = APIRouter()


# Render the dedicated compare workspace without starting transformation work.
@router.get("/compare")
def page(request: Request):
    return tool_page(request, "compare")


# Process typed pasted content on the bounded application worker pool.
@router.post("/api/v1/compare")
def run(payload: CompareOptions):
    return respond(compare(payload))

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from app.catalog import available_tools, find_tool

ROOT = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(ROOT / "templates"))
TEMPLATES.env.globals["navigation_tools"] = tuple(available_tools())


# Render a dedicated service template with shared navigation and catalog metadata.
def tool_page(request: Request, slug: str) -> Response:
    return TEMPLATES.TemplateResponse(
        request=request, name=f"tools/{slug}.html", context={"tool": find_tool(slug), "page": slug}
    )

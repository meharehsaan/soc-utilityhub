from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.catalog import find_tool

ROOT = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(ROOT / "templates"))


# Render a dedicated service template with shared navigation and catalog metadata.
def tool_page(request: Request, slug: str):
    return TEMPLATES.TemplateResponse(
        request=request, name=f"tools/{slug}.html", context={"tool": find_tool(slug), "page": slug}
    )

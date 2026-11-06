from contextlib import asynccontextmanager

import anyio.to_thread
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.catalog import available_tools
from app.core.errors import ToolError, error_response
from app.core.security import SafetyMiddleware
from app.routers import (
    certificate,
    cidr,
    compare,
    cron,
    email,
    encoder,
    entropy,
    events,
    hash,
    http_status,
    ioc,
    json,
    jwt,
    logs,
    mac,
    process_tree,
    query,
    regex,
    report,
    sanitize,
    sigma,
    signature,
    spell,
    stix,
    strings,
    text,
    timeline,
    timestamp,
    unicode,
    url,
    user_agent,
    user_sid,
)
from app.web import ROOT, TEMPLATES


# Cap synchronous tool work independently of the number of inbound connections.
@asynccontextmanager
async def lifespan(app: FastAPI):
    anyio.to_thread.current_default_thread_limiter().total_tokens = 4
    yield


# Assemble a fresh application without starting servers or loading heavy tool resources.
def create_app() -> FastAPI:
    app = FastAPI(
        title="Utility Hub",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(SafetyMiddleware)
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    # Return safe public failures without echoing submitted documents or field values.
    @app.exception_handler(ToolError)
    async def handle_tool_error(request: Request, exc: ToolError):
        return error_response(exc)

    # Expose validation locations and messages without Pydantic's sensitive input fields.
    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError):
        fields = [
            {"field": ".".join(str(part) for part in issue["loc"]), "message": issue["msg"]}
            for issue in exc.errors()
        ]
        return JSONResponse(
            {
                "error": {
                    "code": "invalid_options",
                    "message": "Check the submitted options.",
                    "fields": fields,
                }
            },
            status_code=422,
        )

    # Keep framework errors consistent while withholding internal exception details.
    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, exc: HTTPException):
        return error_response(
            ToolError("Request not found or not supported.", "http_error", exc.status_code)
        )

    # Serve the searchable catalog of implemented tools only.
    @app.get("/")
    def homepage(request: Request):
        return TEMPLATES.TemplateResponse(
            request=request, name="home.html", context={"tools": available_tools(), "page": "home"}
        )

    # Explain actual processing and safe usage without exposing filesystem documents.
    @app.get("/guide")
    def guide(request: Request):
        return TEMPLATES.TemplateResponse(
            request=request, name="guide.html", context={"page": "guide"}
        )

    # Provide a data-free startup probe for local operators and tests.
    @app.get("/health")
    def health():
        return {"status": "ok"}

    for router in (
        sanitize.router,
        text.router,
        logs.router,
        json.router,
        hash.router,
        encoder.router,
        compare.router,
        regex.router,
        signature.router,
        user_agent.router,
        cron.router,
        cidr.router,
        mac.router,
        user_sid.router,
        http_status.router,
        entropy.router,
        ioc.router,
        timestamp.router,
        url.router,
        email.router,
        jwt.router,
        timeline.router,
        events.router,
        query.router,
        sigma.router,
        process_tree.router,
        certificate.router,
        strings.router,
        unicode.router,
        stix.router,
        report.router,
        spell.router,
    ):
        app.include_router(router)

    return app

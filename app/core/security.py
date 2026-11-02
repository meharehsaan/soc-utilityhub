from urllib.parse import urlsplit

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import ToolError, error_response

MIB = 1024 * 1024


class SafetyMiddleware:
    # Keep request limits and security state scoped to this application instance.
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.active = 0

    # Reject oversized or cross-site work before multipart parsing or execution.
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope["headers"]}
        path, method = scope["path"], scope["method"]
        limit = 50 * MIB + 128 * 1024 if path == "/api/v1/hash/file" else 5 * MIB
        if path.startswith("/api/v1/compare"):
            limit = 10 * MIB
        consumed, started = 0, False

        # Count actual body chunks even when content length is missing or misleading.
        async def limited_receive() -> Message:
            nonlocal consumed
            message = await receive()
            consumed += len(message.get("body", b""))
            if consumed > limit:
                raise ToolError("Input exceeds this tool's request limit.", "input_too_large", 413)
            return message

        # Attach a restrictive policy without allowing inline scripts or unsafe markup.
        async def secured_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                extra = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"x-frame-options", b"DENY"),
                    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                    (
                        b"content-security-policy",
                        b"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; font-src 'self'; connect-src 'self'; worker-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
                    ),
                ]
                if not path.startswith("/static/"):
                    extra.append((b"cache-control", b"no-store"))
                message = {**message, "headers": list(message.get("headers", [])) + extra}
            await send(message)

        try:
            lengths = [v for k, v in scope["headers"] if k.lower() == b"content-length"]
            if len(lengths) > 1:
                raise ToolError("Ambiguous content length.")
            if lengths:
                try:
                    size = int(lengths[0])
                except ValueError as exc:
                    raise ToolError("Invalid content length.") from exc
                if size < 0:
                    raise ToolError("Invalid content length.")
                if size > limit:
                    raise ToolError(
                        "Input exceeds this tool's request limit.", "input_too_large", 413
                    )
            if method in {"POST", "PUT", "PATCH", "DELETE"}:
                origin = headers.get("origin")
                if headers.get("sec-fetch-site") == "cross-site" or (
                    origin
                    and (
                        urlsplit(origin).netloc.lower() != headers.get("host", "").lower()
                        or urlsplit(origin).scheme != scope["scheme"]
                    )
                ):
                    raise ToolError("Cross-site submissions are not accepted.", "cross_site", 403)
            if method == "POST" and self.active >= 8:
                raise ToolError("Tools are busy; please retry shortly.", "busy", 429)
            if method == "POST":
                self.active += 1
            try:
                await self.app(scope, limited_receive, secured_send)
            finally:
                if method == "POST":
                    self.active -= 1
        except ToolError as exc:
            if started:
                raise
            await error_response(exc)(scope, receive, secured_send)

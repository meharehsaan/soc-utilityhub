from starlette.responses import JSONResponse


class ToolError(Exception):
    # Carry a safe public error without recording user input.
    def __init__(self, message: str, code: str = "invalid_input", status: int = 400) -> None:
        self.message, self.code, self.status = message, code, status
        super().__init__(message)


# Return a consistent error body that never includes the submitted document.
def error_response(error: ToolError) -> JSONResponse:
    return JSONResponse(
        {"error": {"code": error.code, "message": error.message}}, status_code=error.status
    )

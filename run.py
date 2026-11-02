import argparse

import uvicorn


# Start every implemented tool through one configurable application entry point.
def main() -> None:
    parser = argparse.ArgumentParser(description="Run Utility Hub locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="Enable local development reload.")
    options = parser.parse_args()
    if not 1 <= options.port <= 65535:
        parser.error("port must be between 1 and 65535")
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=options.host,
        port=options.port,
        reload=options.reload,
        access_log=False,
        limit_concurrency=24,
        timeout_keep_alive=5,
        server_header=False,
    )


if __name__ == "__main__":
    main()

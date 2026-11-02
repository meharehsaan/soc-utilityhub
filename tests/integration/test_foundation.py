import asyncio
import unittest

import httpx
from fastapi import Request

from app.main import create_app


class FoundationTests(unittest.IsolatedAsyncioTestCase):
    # Create an isolated application so request counters never leak between tests.
    async def asyncSetUp(self) -> None:
        self.heartbeat = asyncio.create_task(self.tick_loop())
        self.app = create_app()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app), base_url="http://testserver"
        )

    # Release the in-process client without opening a network connection.
    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        self.heartbeat.cancel()
        try:
            await self.heartbeat
        except asyncio.CancelledError:
            pass

    # Keep in-process worker wakeups moving like Uvicorn's periodic server tick.
    async def tick_loop(self) -> None:
        while True:
            await asyncio.sleep(0.02)

    # Verify the real templates and static files are wired to the single application.
    async def test_pages_and_assets(self) -> None:
        for path in ("/", "/guide", "/static/css/app.css", "/static/js/theme.js"):
            with self.subTest(path=path):
                response = await self.client.get(path)
                self.assertEqual(response.status_code, 200)
        self.assertEqual((await self.client.get("/health")).json(), {"status": "ok"})

    # Reject cross-site POSTs even when they target a non-existent service.
    async def test_cross_site_submission(self) -> None:
        response = await self.client.post(
            "/api/v1/missing", headers={"Origin": "https://elsewhere.test"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "cross_site")

    # Enforce declared sizes before parsing potentially hostile upload bodies.
    async def test_declared_body_limit(self) -> None:
        response = await self.client.post(
            "/api/v1/missing", content=b"x", headers={"Content-Length": "6000000"}
        )
        self.assertEqual(response.status_code, 413)

    # Limit streamed bodies without trusting a content-length header.
    async def test_streamed_body_limit(self) -> None:
        # Consume the actual ASGI body to exercise enforcement during reads.
        @self.app.post("/consume")
        async def consume(request: Request):
            await request.body()
            return {"status": "accepted"}

        # Stream an oversized payload rather than constructing a misleading declaration.
        async def chunks():
            for _ in range(6):
                yield b"x" * 1024 * 1024

        response = await self.client.post("/consume", content=chunks())
        self.assertEqual(response.status_code, 413)

    # Protect result pages from caching and unsafe framing or inline execution.
    async def test_security_headers(self) -> None:
        response = await self.client.get("/")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertIn("frame-ancestors 'none'", response.headers["content-security-policy"])
        self.assertNotIn("unsafe-inline", response.headers["content-security-policy"])


if __name__ == "__main__":
    unittest.main()

import asyncio
import unittest

import httpx

from app.main import create_app


class ASGITestCase(unittest.IsolatedAsyncioTestCase):
    # Create an isolated application so request counters never leak between tests.
    async def asyncSetUp(self) -> None:
        self.heartbeat = asyncio.create_task(self.tick_loop())
        self.app = create_app()
        self.lifecycle = self.app.router.lifespan_context(self.app)
        await self.lifecycle.__aenter__()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app), base_url="http://testserver"
        )

    # Release the in-process client without opening a network connection.
    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await self.lifecycle.__aexit__(None, None, None)
        self.heartbeat.cancel()
        try:
            await self.heartbeat
        except asyncio.CancelledError:
            pass

    # Keep in-process worker wakeups moving like Uvicorn's periodic server tick.
    async def tick_loop(self) -> None:
        while True:
            await asyncio.sleep(0.02)

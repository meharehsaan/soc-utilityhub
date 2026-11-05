from html import unescape

from app.catalog import available_tools
from tests.integration.base import ASGITestCase


class InvestigationAPITests(ASGITestCase):
    # Render every catalog page through the real template and routing layer.
    async def test_catalog_pages(self) -> None:
        for tool in available_tools():
            with self.subTest(slug=tool.slug):
                response = await self.client.get("/" + tool.slug)
                self.assertEqual(response.status_code, 200)
                self.assertIn(tool.name, unescape(response.text))
                self.assertIn("/static/js/tools/" + tool.slug + ".js", response.text)

    # Exercise added service endpoints with small synthetic inputs and no network sockets.
    async def test_investigation_operations(self) -> None:
        cases = {
            "timestamp": {"text": "2026-01-01T00:00:00Z"},
            "url": {"text": "https://example.test/?x=one&x=two"},
            "ioc": {"text": "192.0.2.1"},
            "email": {"text": "Content-Type: text/plain; charset=utf-8\n\nhello 😀"},
            "jwt": {"text": "eyJhbGciOiJub25lIn0.eyJzdWIiOiJzYW1wbGUifQ."},
            "query": {"text": 'one"two'},
            "unicode": {"text": "a\u200bb"},
            "strings": {"text": "hello"},
            "timeline": {"text": '{"timestamp":"2026-01-01T00:00:00Z","action":"read"}'},
            "process-tree": {
                "text": '{"Computer":"synthetic","ProcessGuid":"one","Image":"sample"}'
            },
            "events": {"text": "", "mode": "lookup"},
            "stix": {"text": "192.0.2.1", "mode": "export"},
            "report": {"text": "Supplied evidence only"},
        }
        for slug, payload in cases.items():
            with self.subTest(slug=slug):
                response = await self.client.post("/api/v1/" + slug, json=payload)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertIsInstance(response.json()["output"], str)

    # Keep raw MIME bytes intact across the multipart upload endpoint.
    async def test_raw_email_upload(self) -> None:
        response = await self.client.post(
            "/api/v1/email/file",
            files={
                "file": (
                    "synthetic.eml",
                    b"Content-Type: text/plain; charset=latin-1\r\n\r\ncaf\xe9",
                )
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("café", response.json()["output"])

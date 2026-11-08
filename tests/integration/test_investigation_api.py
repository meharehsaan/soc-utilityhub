import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

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

    # Browser-only services expose pages and reject server-side processing submissions.
    async def test_browser_processing_boundary(self) -> None:
        slugs = [
            "encoder",
            "regex",
            "signature",
            "user-agent",
            "cron",
            "cidr",
            "mac",
            "user-sid",
            "http-status",
            "entropy",
        ]
        for slug in slugs:
            with self.subTest(slug=slug):
                response = await self.client.post(
                    "/api/v1/" + slug, json={"text": "synthetic private input"}
                )
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.headers["cache-control"], "no-store")

    # Unexpected parser failures must never print submitted strings or internal tracebacks.
    async def test_unexpected_failure_privacy(self) -> None:
        # Simulate an internal parser error containing synthetic sensitive text.
        @self.app.post("/synthetic-error")
        def fail_parser() -> None:
            raise ValueError("synthetic-sensitive-content")

        with self.assertLogs("utility_hub", level="ERROR") as captured:
            response = await self.client.post("/synthetic-error")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "processing_failed")
        self.assertNotIn("synthetic-sensitive-content", response.text)
        self.assertNotIn("synthetic-sensitive-content", "".join(captured.output))
        self.assertNotIn("Traceback", "".join(captured.output))

    # Signature styling, font, and all catalog assets must resolve locally.
    async def test_local_catalog_assets(self) -> None:
        for tool in available_tools():
            with self.subTest(slug=tool.slug):
                response = await self.client.get("/static/js/tools/" + tool.slug + ".js")
                self.assertEqual(response.status_code, 200)
        page = await self.client.get("/signature")
        self.assertIn("/static/css/signature.css", page.text)
        font = await self.client.get("/static/fonts/DejaVuSerif.ttf")
        self.assertEqual(font.status_code, 200)

    # Catch missing template controls before browser controllers dereference their elements.
    async def test_controller_template_bindings(self) -> None:
        for tool in available_tools():
            with self.subTest(slug=tool.slug):
                page = await self.client.get("/" + tool.slug)
                parser = ControlParser()
                parser.feed(page.text)
                script = (Path("app/static/js/tools") / (tool.slug + ".js")).read_text()
                for element_id in re.findall(r'getElementById\("([^"]+)"\)', script):
                    self.assertIn(element_id, parser.ids, tool.slug + ": " + element_id)
                for field in re.findall(r'(?:value|checked)\("([^"]+)"\)', script):
                    self.assertIn(field, parser.names, tool.slug + ": " + field)
        signature = await self.client.get("/signature")
        self.assertIn('id="signature-pad"', signature.text)
        timeline = await self.client.get("/timeline")
        self.assertIn('id="source-file" multiple', timeline.text)


class ControlParser(HTMLParser):
    # Keep inert control names and IDs for structural template checks.
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.names: set[str] = set()

    # Collect only attributes without loading resources or interpreting markup.
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        if values.get("name"):
            self.names.add(values["name"])

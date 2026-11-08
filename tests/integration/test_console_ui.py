import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from app.catalog import available_tools
from tests.integration.base import ASGITestCase


class ShellParser(HTMLParser):
    # Collect rendered shell IDs and local resources without interpreting the page.
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.resources: list[str] = []

    # Read only ID and resource attributes needed for frontend regression checks.
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "script" and values.get("src"):
            self.resources.append(values["src"])
        if tag == "link" and values.get("rel") in {"stylesheet", "preload"}:
            self.resources.append(values.get("href", ""))


class ConsoleUITests(ASGITestCase):
    # Check the new shared navigation bindings and unique IDs on every service page.
    async def test_shared_shell_bindings(self) -> None:
        script = Path("app/static/js/shell.js").read_text()
        required = re.findall(r'getElementById\("([^"]+)"\)', script)
        self.assertGreaterEqual(len(required), 6)
        for tool in available_tools():
            with self.subTest(slug=tool.slug):
                response = await self.client.get("/" + tool.slug)
                parser = ShellParser()
                parser.feed(response.text)
                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                for element_id in required:
                    self.assertIn(element_id, parser.ids)
                self.assertIn('data-tool="' + tool.slug + '"', response.text)
                self.assertIn('data-icon="' + tool.slug + '"', response.text)
                self.assertIn("tool-form", parser.ids)
                self.assertIn("result-output", parser.ids)

    # Keep console chrome small and local without a framework, CDN, or font download.
    async def test_ui_asset_budget_and_local_resources(self) -> None:
        response = await self.client.get("/")
        self.assertLess(len(response.content), 96 * 1024)
        parser = ShellParser()
        parser.feed(response.text)
        self.assertTrue(parser.resources)
        self.assertTrue(all(path.startswith("/static/") for path in parser.resources))
        self.assertNotIn("fonts.googleapis.com", response.text)
        self.assertLess(Path("app/static/css/app.css").stat().st_size, 48 * 1024)
        self.assertLess(Path("app/static/js/shell.js").stat().st_size, 5 * 1024)
        self.assertNotIn("unsafe-inline", response.headers["content-security-policy"])

    # Display actual service counts and all local service identities in the catalog.
    async def test_catalog_counts_and_identities(self) -> None:
        response = await self.client.get("/")
        self.assertEqual(response.text.count('class="tool-card accent-'), 32)
        counts = Counter(tool.processing for tool in available_tools())
        self.assertEqual(
            counts, {"In your browser": 10, "On your server": 21, "Choose browser or server": 1}
        )
        self.assertIn('id="visible-count"', response.text)
        self.assertIn('class="dark" data-theme="dark"', response.text)

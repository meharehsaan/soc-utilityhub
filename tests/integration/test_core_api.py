import io

from tests.integration.base import ASGITestCase


class CoreAPITests(ASGITestCase):
    # All seven pages expose a dedicated safe controller.
    async def test_tool_pages_and_assets(self) -> None:
        for slug in ("sanitize", "text", "logs", "json", "hash", "encoder", "compare"):
            with self.subTest(slug=slug):
                page = await self.client.get(f"/{slug}")
                self.assertEqual(page.status_code, 200)
                self.assertIn(f"/static/js/tools/{slug}.js", page.text)
                self.assertEqual(
                    (await self.client.get(f"/static/js/tools/{slug}.js")).status_code, 200
                )

    # Server transformations return the public result shape without caching content.
    async def test_pasted_operations(self) -> None:
        cases = {
            "sanitize": {
                "text": "alice",
                "replacements": [{"category": "username", "source": "alice"}],
            },
            "text": {"text": "b\na"},
            "logs": {"text": '{"host":"web-01"}'},
            "json": {"text": '{"id":9007199254740993}'},
            "hash": {"text": "abc"},
            "compare": {"a": "a\nb", "b": "b"},
        }
        for slug, payload in cases.items():
            with self.subTest(slug=slug):
                response = await self.client.post(f"/api/v1/{slug}", json=payload)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertIn("output", response.json())
                self.assertEqual(response.headers["cache-control"], "no-store")

    # Multipart text uploads reuse typed options and preserve trailing newlines.
    async def test_text_upload(self) -> None:
        response = await self.client.post(
            "/api/v1/text/file",
            files={"file": ("sample.txt", b"b\na\n")},
            data={"options": '{"action":"sort"}'},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["output"], "a\nb\n")

    # Uploaded names are inert labels rather than filesystem paths.
    async def test_binary_hash_upload(self) -> None:
        response = await self.client.post(
            "/api/v1/hash/file",
            files={"file": ("../../sensitive.exe", io.BytesIO(b"%PDF-1.7\n\x00\xff"))},
            data={"algorithms": '["sha256"]'},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["meta"]["extension_mismatch"])

    # Unexpected file slots fail instead of silently discarding extra uploads.
    async def test_reject_extra_uploads(self) -> None:
        response = await self.client.post(
            "/api/v1/text/file", files=[("file", ("a.txt", b"a")), ("second", ("b.txt", b"b"))]
        )
        self.assertEqual(response.status_code, 400)

    # Public validation errors omit submitted values and internal input snapshots.
    async def test_validation_privacy(self) -> None:
        secret = "PRIVATE_VALUE_DO_NOT_ECHO"
        response = await self.client.post("/api/v1/text", json={"text": secret, "action": secret})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(secret, response.text)
        self.assertNotIn("input", response.json()["error"]["fields"][0])

    # Browser-only encoding has no accidental upload endpoint.
    async def test_no_browser_upload_endpoint(self) -> None:
        self.assertEqual(
            (await self.client.post("/api/v1/encoder", json={"text": "private"})).status_code, 404
        )

    # Hostile markup remains data rather than being inserted into an HTML document.
    async def test_html_remains_data(self) -> None:
        source = '<script>alert("x")</script>'
        response = await self.client.post("/api/v1/text", json={"text": source})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["output"], source)

    # Malformed origins are rejected with security headers rather than causing a server error.
    async def test_malformed_origin(self) -> None:
        response = await self.client.post(
            "/api/v1/text", json={"text": "private"}, headers={"Origin": "https://["}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.headers["cache-control"], "no-store")

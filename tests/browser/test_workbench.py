import os
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("UTILITY_HUB_TEST_URL")
if not BASE_URL:
    pytest.skip(
        "Start run.py and set UTILITY_HUB_TEST_URL for real-browser checks.",
        allow_module_level=True,
    )


# Exercise theme parity and responsive navigation on an actual running application.
@pytest.mark.parametrize("theme", ["dark", "light"])
def test_home_theme_and_search(page: Page, theme: str) -> None:
    page.goto(BASE_URL)
    if page.locator("html").get_attribute("data-theme") != theme:
        page.get_by_role("button", name=f"Switch to {theme} mode").click()
    expect(page.locator("html")).to_have_attribute("data-theme", theme)
    page.get_by_role("searchbox", name="Search tools").fill("sanitizer")
    expect(page.locator(".tool-card:visible")).to_have_count(1)
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    Path("test-results").mkdir(exist_ok=True)
    page.screenshot(path=f"test-results/home-{theme}.png", full_page=True)


# Verify literal redaction and its review preview through the real browser/backend path.
def test_sanitizer(page: Page) -> None:
    page.goto(f"{BASE_URL}/sanitize")
    page.get_by_role("button", name="Try an example").click()
    page.get_by_role("button", name="Replace & preview").click()
    expect(page.locator("#result-output")).to_contain_text("EMAIL_001")
    assert "alice@acme.test" not in page.locator("#result-output").text_content()
    page.get_by_role("button", name="Reset", exact=True).click()
    expect(page.locator("#source")).to_have_value("")
    expect(page.locator("#result-empty")).to_be_visible()


# Collapsing a JSON branch must not mutate the complete lossless output.
def test_json_tree_preserves_output(page: Page) -> None:
    page.goto(f"{BASE_URL}/json")
    page.get_by_role("button", name="Try an example").click()
    page.get_by_role("button", name="Run tool").click()
    expect(page.locator("#json-tree")).to_contain_text("9007199254740993")
    before = page.locator("#result-output").text_content()
    page.get_by_role("button", name="Collapse all").click()
    assert page.locator("#result-output").text_content() == before
    page.locator("#tree-search").fill("host")
    expect(page.locator("#json-tree")).to_contain_text("web-01")


# Encoding must stay local while the rendered result remains inert text.
def test_encoder_does_not_upload(page: Page) -> None:
    submissions = []

    # Record only network submissions, not local static-asset reads.
    def observe(request) -> None:
        if request.method == "POST":
            submissions.append(request.url)

    page.on("request", observe)
    page.goto(f"{BASE_URL}/encoder")
    page.get_by_role("button", name="Try an example").click()
    page.get_by_role("button", name="Run tool").click()
    expect(page.locator("#result-output")).to_contain_text("Hello, analyst.")
    assert submissions == []


# Raw file hashing in browser mode must match the known vector without an upload.
def test_browser_hash(page: Page) -> None:
    page.goto(f"{BASE_URL}/hash")
    page.get_by_role("button", name="Try an example").click()
    page.get_by_role("button", name="Run tool").click()
    expect(page.locator("#result-output")).to_contain_text("900150983cd24fb0d6963f7d28e17f72")

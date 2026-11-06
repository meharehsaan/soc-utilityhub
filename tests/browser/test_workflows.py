import pytest
from playwright.sync_api import Page, expect

BROWSER_TOOLS = [
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


# Use the explicitly supplied local app URL without starting or contacting a remote service.
@pytest.fixture
def hub_url(base_url: str | None) -> str:
    return base_url or "http://127.0.0.1:8000"


# Check actual browser engines, local workers, and rendered controls in both themes.
@pytest.mark.parametrize("theme", ["dark", "light"])
@pytest.mark.parametrize("slug", BROWSER_TOOLS)
def test_local_tools_do_not_submit_inputs(page: Page, hub_url: str, theme: str, slug: str) -> None:
    submissions = []

    # Record any unexpected content submission from a browser-only service.
    def record_request(request) -> None:
        if request.method not in {"GET", "HEAD"}:
            submissions.append(request.url)

    page.on("request", record_request)
    page.goto(hub_url + "/" + slug)
    if theme == "light":
        page.get_by_role("button", name="Switch to light mode").click()
    expect(page.locator("html")).to_have_attribute("data-theme", theme)
    page.get_by_role("button", name="Try an example").click()
    page.locator("#run-tool").click()
    expect(page.locator("#result-empty")).to_be_hidden(timeout=15000)
    expect(page.locator("#tool-error")).to_be_hidden()
    expect(page.locator("#download-result")).to_be_enabled()
    assert submissions == []
    stored = page.evaluate(
        "() => ({local:Object.keys(localStorage),session:Object.keys(sessionStorage)})"
    )
    assert set(stored["local"]) <= {"utility-hub-theme"}
    assert stored["session"] == []
    page.get_by_role("button", name="Reset", exact=True).click()
    expect(page.locator("#result-empty")).to_be_visible()


# Exercise real template bindings and lossless JSON export while hiding tree branches.
def test_json_tree_pin_and_export(page: Page, hub_url: str) -> None:
    page.goto(hub_url + "/json")
    page.locator("#source").fill(
        '{"id":9007199254740993,"branch":{"email":"example@example.test"}}'
    )
    page.locator("#run-tool").click()
    expect(page.locator("#json-tree")).to_be_visible()
    page.get_by_role("button", name="Pin JSON field id", exact=True).click()
    expect(page.locator("#json-pins")).to_contain_text("9007199254740993")
    page.get_by_role("button", name="Collapse all", exact=True).click()
    expect(page.locator("#result-output")).to_contain_text('"email": "example@example.test"')
    page.get_by_role("button", name="Pretty", exact=True).click()
    expect(page.locator("#result-output")).to_contain_text("9007199254740993")


# Check readable responsive layouts and local catalog filtering without navigation.
@pytest.mark.parametrize("width", [390, 1280])
@pytest.mark.parametrize("theme", ["dark", "light"])
def test_home_layout_and_search(page: Page, hub_url: str, width: int, theme: str) -> None:
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(hub_url)
    if theme == "light":
        page.get_by_role("button", name="Switch to light mode").click()
    expect(page.locator(".tool-card")).to_have_count(32)
    page.locator("#tool-search").fill("sanitize")
    expect(page.locator(".tool-card:visible")).to_have_count(1)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

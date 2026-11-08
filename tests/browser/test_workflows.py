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


# Desktop collapse must not leave an offset when the same page becomes mobile.
def test_sidebar_collapse_and_mobile_resize(page: Page, hub_url: str) -> None:
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(hub_url + "/json")
    page.get_by_role("button", name="Collapse sidebar", exact=True).click()
    expect(page.get_by_role("button", name="Expand sidebar", exact=True)).to_be_visible()
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(350)
    assert page.locator("#app-column").evaluate("node => node.getBoundingClientRect().left") == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


# Mobile navigation traps focus, supports Escape, and retains service input.
def test_mobile_navigation_keeps_workbench_state(page: Page, hub_url: str) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(hub_url + "/text")
    page.locator("#source").fill("Retain this synthetic input")
    page.get_by_role("button", name="Open navigation", exact=True).click()
    expect(page.locator("#app-sidebar")).to_have_class("app-sidebar open")
    assert page.locator("#app-column").evaluate("node => node.inert")
    page.keyboard.press("Escape")
    expect(page.get_by_role("button", name="Open navigation", exact=True)).to_be_focused()
    expect(page.locator("#source")).to_have_value("Retain this synthetic input")
    assert not page.locator("#app-column").evaluate("node => node.inert")


# Both theme selectors stay synchronized without resetting form content.
def test_theme_switch_preserves_service_input(page: Page, hub_url: str) -> None:
    page.goto(hub_url + "/text")
    page.locator("#source").fill("Keep this content")
    page.get_by_role("button", name="Switch to light mode", exact=True).click()
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    expect(page.locator("html")).not_to_have_class("dark")
    expect(page.locator("#source")).to_have_value("Keep this content")


# Sidebar category entry points and local search share the same catalog state.
def test_category_entry_point_and_empty_search(page: Page, hub_url: str) -> None:
    page.goto(hub_url + "/?category=Investigation#catalog")
    expect(page.locator('.filter[data-category="Investigation"]')).to_have_attribute(
        "aria-pressed", "true"
    )
    page.locator("#tool-search").fill("no-such-synthetic-tool")
    expect(page.locator("#empty-search")).to_be_visible()
    expect(page.locator("#visible-count")).to_have_text("0")
    page.locator("#tool-search").fill("")
    expect(page.locator("#empty-search")).to_be_hidden()


# Card feedback uses service colors and a small desktop tilt without changing navigation.
@pytest.mark.parametrize("theme", ["dark", "light"])
def test_card_hover_and_soc_branding(page: Page, hub_url: str, theme: str) -> None:
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(hub_url)
    if theme == "light":
        page.get_by_role("button", name="Switch to light mode", exact=True).click()
    card = page.locator(".tool-card").first
    before = card.evaluate("node => getComputedStyle(node).backgroundColor")
    expect(card.locator(".card-watermark")).to_have_attribute("aria-hidden", "true")
    expect(card).to_have_css("border-left-width", "5px")
    card.hover()
    expect(card).not_to_have_css("transform", "none")
    expect(card).not_to_have_css("background-color", before)
    expect(page.locator(".footer-credit")).to_contain_text("Created by Ehsaan Mehar")
    expect(page.locator(".github-button")).to_have_attribute(
        "href", "https://github.com/meharehsaan"
    )
    expect(page.locator(".github-button")).to_have_attribute("rel", "noopener noreferrer")
    page.emulate_media(reduced_motion="reduce")
    expect(card).to_have_css("transform", "none")
    expect(card.locator(".card-watermark")).to_have_css("transform", "none")

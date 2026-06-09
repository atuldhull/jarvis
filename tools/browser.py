"""Browser tools (Phase 3) — drive a real browser with Playwright.

This is the workhorse for "do anything on the web". It stays logged in by using a
persistent profile folder (config.BROWSER_PROFILE): log into a site once by hand in
JARVIS's browser window, and the cookies persist for every later run.

Design note: these are deliberately small, hand-written *skills* the model selects
by name (open, type, click, read, plus YouTube convenience skills) — far more
reliable on a small local model than fully-autonomous browsing.

Playwright is imported lazily, so importing this module is harmless even before
you've run `playwright install`. The browser launches on the first browser tool
the model actually calls.
"""

import urllib.parse

import config

from .registry import tool

_page = None
_ctx = None
_pw = None


def _page_handle():
    """Launch (once) and return the live browser page."""
    global _page, _ctx, _pw
    if _page is not None:
        return _page
    from playwright.sync_api import sync_playwright

    _pw = sync_playwright().start()
    _ctx = _pw.chromium.launch_persistent_context(
        config.BROWSER_PROFILE, channel="msedge", headless=False, no_viewport=True
    )
    _page = _ctx.pages[0] if _ctx.pages else _ctx.new_page()
    return _page


@tool(
    "browser_open",
    "Open a URL in JARVIS's browser (which stays logged in across runs).",
    {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
)
def browser_open(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    page = _page_handle()
    page.goto(url, wait_until="domcontentloaded")
    return f"Opened {url} — page title: {page.title()!r}"


@tool(
    "browser_click",
    "Click the first element whose visible text matches the given text.",
    {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
)
def browser_click(text):
    page = _page_handle()
    try:
        page.get_by_text(text, exact=False).first.click(timeout=8000)
        return f"Clicked '{text}'."
    except Exception as e:
        return f"Couldn't click '{text}': {e}"


@tool(
    "browser_type",
    "Type text into the currently focused field, optionally pressing Enter.",
    {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "submit": {"type": "boolean", "description": "Press Enter after typing?"},
        },
        "required": ["text"],
    },
)
def browser_type(text, submit=False):
    page = _page_handle()
    page.keyboard.type(text)
    if submit:
        page.keyboard.press("Enter")
    return f"Typed '{text}'" + (" and pressed Enter." if submit else ".")


@tool("browser_read", "Read the visible text of the current page (first ~1500 chars).")
def browser_read():
    page = _page_handle()
    try:
        return page.inner_text("body")[:1500]
    except Exception as e:
        return f"Couldn't read the page: {e}"


# ── Hand-written convenience skills for the user's exact goal ──────────────────

@tool(
    "youtube_search",
    "Open YouTube and search for a query.",
    {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
)
def youtube_search(query):
    page = _page_handle()
    page.goto(
        "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query),
        wait_until="domcontentloaded",
    )
    return f"Searched YouTube for '{query}'."


@tool("youtube_play_first", "Play the first video on the current YouTube search results page.")
def youtube_play_first():
    page = _page_handle()
    try:
        page.locator("a#video-title").first.click(timeout=8000)
        return "Playing the first result, sir."
    except Exception as e:
        return f"Couldn't play the first result: {e}"

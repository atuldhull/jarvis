"""Web tools — open websites and searches in the default browser.

These are the simple, no-dependency web actions. The richer, stay-logged-in
browser control (clicking, typing, reading pages) lives in browser.py (Phase 3).
"""

import urllib.parse
import webbrowser

from .registry import tool


@tool(
    "open_website",
    "Open a website URL in the default browser.",
    {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Full URL, e.g. https://youtube.com"}
        },
        "required": ["url"],
    },
)
def open_website(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}."


@tool(
    "web_search",
    "Search the web for a query (opens the results page in the default browser).",
    {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
)
def web_search(query):
    webbrowser.open("https://duckduckgo.com/?q=" + urllib.parse.quote(query))
    return f"Searched the web for: {query}"

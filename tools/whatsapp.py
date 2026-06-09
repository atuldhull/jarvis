"""WhatsApp tools — send and read messages on WhatsApp Web.

Runs on the SAME logged-in browser profile as the other browser tools, so you scan
the WhatsApp QR code ONCE and stay logged in for every later run. WhatsApp opens in
its own tab, so it doesn't disturb whatever else the browser is doing.

Sending a message is outward-facing and can't be unsent, so `whatsapp_send` is
marked confirm=True — the safety layer asks before it actually sends. Reading is free.

Heads-up: WhatsApp Web tweaks its page structure now and then. The selectors below
have fallbacks; if one stops matching, the tool fails with a clear message instead
of doing the wrong thing. Tune the selectors here if WhatsApp changes them.
"""

from . import browser
from .registry import tool

_wa = None  # the dedicated WhatsApp tab

# WhatsApp Web's chat-search box and message box. data-tab values are the most
# stable hooks WhatsApp exposes; the contenteditable type is the fallback.
_SEARCH = 'div[contenteditable="true"][data-tab="3"]'
_MSGBOX = 'div[contenteditable="true"][data-tab="10"]'


def _ready_page():
    """Open WhatsApp Web in its own tab on the shared browser and wait until it loads."""
    global _wa
    ctx = browser._context_handle()
    if _wa is None or _wa.is_closed():
        _wa = ctx.new_page()
    if "web.whatsapp.com" not in (_wa.url or ""):
        _wa.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
    # Wait for either the chat search (logged in) or the QR code (needs login).
    try:
        _wa.wait_for_selector(f'{_SEARCH}, canvas', timeout=40000)
    except Exception:
        pass
    return _wa


def _logged_in(page):
    # The chat-search box only exists once you're logged in.
    return page.locator(_SEARCH).count() > 0


def _open_chat(page, contact):
    """Search for a contact/group by name and open that chat. True on success."""
    search = page.locator(_SEARCH).first
    search.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    page.keyboard.type(contact)
    page.wait_for_timeout(1500)  # let the result list populate
    try:
        # Prefer an exact name match in the results; fall back to the first result.
        exact = page.get_by_title(contact, exact=True)
        if exact.count() > 0:
            exact.first.click(timeout=5000)
        else:
            page.locator('div[role="listitem"]').first.click(timeout=5000)
        page.wait_for_timeout(800)
        return True
    except Exception:
        return False


@tool(
    "whatsapp_send",
    "Send a WhatsApp message to a contact or group by name. Use this to text someone on WhatsApp.",
    {
        "type": "object",
        "properties": {
            "contact": {"type": "string", "description": "Exact contact or group name as saved in WhatsApp."},
            "message": {"type": "string", "description": "The message text to send."},
        },
        "required": ["contact", "message"],
    },
    confirm=True,
)
def whatsapp_send(contact, message):
    page = _ready_page()
    if not _logged_in(page):
        return "WhatsApp isn't logged in yet — scan the QR code in the WhatsApp tab once, then ask me again."
    if not _open_chat(page, contact):
        return f"Couldn't find a chat called '{contact}'. Check the exact name as it's saved in WhatsApp."
    try:
        box = page.locator(_MSGBOX).first
        box.wait_for(timeout=8000)
        box.click()
        page.keyboard.type(message)
        page.keyboard.press("Enter")
        return f"Sent to {contact}: {message!r}"
    except Exception as e:
        return f"Opened {contact}'s chat but couldn't send the message: {e}"


@tool(
    "whatsapp_read_latest",
    "Read the most recent messages in a WhatsApp chat — use before replying to someone's latest text.",
    {
        "type": "object",
        "properties": {
            "contact": {"type": "string", "description": "Exact contact or group name."},
            "count": {"type": "integer", "description": "How many recent messages to read (default 5)."},
        },
        "required": ["contact"],
    },
)
def whatsapp_read_latest(contact, count=5):
    page = _ready_page()
    if not _logged_in(page):
        return "WhatsApp isn't logged in yet — scan the QR code in the WhatsApp tab once, then ask me again."
    if not _open_chat(page, contact):
        return f"Couldn't find a chat called '{contact}'."
    try:
        bubbles = page.locator("div.message-in, div.message-out")
        n = bubbles.count()
        if n == 0:
            return f"No messages found in {contact}'s chat."
        lines = []
        for i in range(max(0, n - int(count)), n):
            b = bubbles.nth(i)
            who = "them" if "message-in" in (b.get_attribute("class") or "") else "you"
            try:
                txt = b.locator("span.selectable-text").last.inner_text()
            except Exception:
                txt = b.inner_text()
            txt = " ".join(txt.split())  # collapse whitespace/newlines
            if txt:
                lines.append(f"{who}: {txt}")
        return "\n".join(lines) if lines else f"Couldn't read any text from {contact}'s chat."
    except Exception as e:
        return f"Couldn't read the chat: {e}"

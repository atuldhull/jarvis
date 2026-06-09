"""Phase 3 + 6 smoke test — headless browser + credential vault round-trip.

Needs `playwright` and `keyring` installed. Headless so no window pops up.
Run:  py test_browser.py
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

# ── Phase 6: credential vault round-trip (Windows Credential Manager) ──────────
from memory import vault

vault.set_password("_jarvis_selftest", "secret123")
assert vault.get_password("_jarvis_selftest") == "secret123", "vault mismatch"
vault.delete_password("_jarvis_selftest")
print("vault OK ✅ (stored, read back, deleted a throwaway credential)")

# ── Phase 3: Playwright can drive Edge ────────────────────────────────────────
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()
    page.goto("https://example.com", wait_until="domcontentloaded")
    print("browser OK ✅ — page title:", page.title())
    browser.close()

print("\nPHASE 3 + 6 SMOKE TEST PASSED ✅")

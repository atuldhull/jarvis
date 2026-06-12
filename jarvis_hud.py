"""JARVIS — the HUD (Iron-Man-style desktop interface).

A fullscreen, frameless heads-up display. Type to JARVIS; the red power button
(bottom-right, or Esc) drops you straight back to your normal desktop while JARVIS
keeps running in the background — click it in the taskbar to bring the HUD back.

    py jarvis_hud.py

The face is HTML/Canvas (frontend/), rendered in a native window by pywebview. The
brain is the SAME orchestrator everything else uses (memory + departments + model
router), wired in through window.pywebview.api — so the HUD is just a gorgeous
front-end on the JARVIS you already built.
"""

import json
import os
import sys
import threading

sys.stdout.reconfigure(encoding="utf-8")

try:
    import webview  # pip install pywebview
except ImportError:
    sys.exit("The HUD needs pywebview:  py -m pip install pywebview")

import config

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "frontend", "index.html")


def _has_cloud_keys() -> bool:
    """True if any cloud brain key is configured (controls the HUD's LOCAL/HYBRID tag)."""
    try:
        with open(os.path.join(HERE, config.KEYS_FILE), encoding="utf-8") as f:
            data = json.load(f)
        for provider in ("gemini", "groq", "openrouter"):
            if any((k or "").strip() for k in data.get(provider, [])):
                return True
    except Exception:
        pass
    return any(os.environ.get(v) for v in ("GEMINI_KEY_1", "GROQ_KEY_1", "OPENROUTER_KEY_1"))


class JarvisAPI:
    """The bridge the HUD's JavaScript calls into (window.pywebview.api.*)."""

    def __init__(self):
        self._window = None
        self._brain = None
        self._lock = threading.Lock()

    def attach(self, window):
        self._window = window

    def _orchestrator(self):
        # Build the brain lazily on first message — loading memory/embeddings takes
        # a beat, so the HUD paints instantly instead of stalling on startup.
        if self._brain is None:
            with self._lock:
                if self._brain is None:
                    from agents.orchestrator import Orchestrator
                    self._brain = Orchestrator()
        return self._brain

    # ── called from the front-end ───────────────────────────────────────────
    def info(self):
        """Static facts for the HUD's status readouts."""
        return {"model": config.MODEL, "name": "JARVIS", "cloud": _has_cloud_keys()}

    def ask(self, text):
        """One turn: user text in → JARVIS's reply out (full orchestrator)."""
        text = (text or "").strip()
        if not text:
            return ""
        try:
            return self._orchestrator().handle(text)
        except Exception as e:
            # Most common cause: Ollama not running, or the model isn't pulled.
            return f"I hit a snag, sir — {e}"

    def power_off(self):
        """'Switch off' → minimize the HUD, back to your normal desktop. JARVIS stays
        alive; bring it back from the taskbar (a global hotkey is the next upgrade)."""
        if self._window:
            self._window.minimize()
        return True


def main():
    api = JarvisAPI()
    window = webview.create_window(
        "JARVIS",
        url=INDEX,
        js_api=api,
        fullscreen=True,
        frameless=True,
        background_color="#04070d",
        text_select=False,
    )
    api.attach(window)
    webview.start(debug=False)


if __name__ == "__main__":
    main()

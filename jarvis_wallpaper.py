"""JARVIS — the living wallpaper (Layer 1 of the desktop HUD).

Renders the reactor + telemetry as your actual desktop BACKGROUND: pinned behind
the icons, full-screen, can't be moved. Your icons and windows sit on top of it,
exactly like a normal wallpaper — except this one is alive.

    py jarvis_wallpaper.py

How it works: we create our window, then slot it into the desktop's wallpaper layer.
On older Windows that's a hidden "WorkerW" window; on newer Win11 (where the icons
hang straight off "Progman") we parent into Progman and drop the window to the bottom
of the z-order so it sits *behind* the icons. Press Ctrl+C in this terminal to stop.

This layer is VISUAL ONLY — a behind-the-icons window can't receive clicks (Windows
sends those to the icons). The clickable buttons live in the floating dock (Layer 2).
"""

import ctypes
from ctypes import wintypes
import os
import sys
import threading
import time

import webview

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "frontend", "wallpaper.html")
TITLE = "JARVIS-WALLPAPER"

# ── Win32 plumbing ───────────────────────────────────────────────────────────
user32 = ctypes.windll.user32
user32.FindWindowW.restype = wintypes.HWND
user32.FindWindowExW.restype = wintypes.HWND
user32.FindWindowExW.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.SetParent.restype = wintypes.HWND
user32.SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
user32.GetParent.restype = wintypes.HWND
user32.GetParent.argtypes = [wintypes.HWND]
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, wintypes.UINT]
_getlong = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
_setlong = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
_getlong.restype = ctypes.c_longlong
_getlong.argtypes = [wintypes.HWND, ctypes.c_int]
_setlong.restype = ctypes.c_longlong
_setlong.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_longlong]

GWL_STYLE = -16
WS_CHILD = 0x40000000
WS_POPUP = 0x80000000
HWND_TOP = 0
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_FRAMECHANGED = 0x0020


def _screen():
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)  # primary W, H


def _wallpaper_target():
    """Return (target_hwnd, layout) — the window to parent into so we render as wallpaper."""
    progman = user32.FindWindowW("Progman", None)
    # Nudge Progman to spawn its wallpaper WorkerW; SendMessageTimeout waits for it.
    res = wintypes.DWORD()
    user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0x0000, 1000, ctypes.byref(res))

    # New Win11 layout (yours): a WorkerW lives as a CHILD of Progman, sitting just
    # below SHELLDLL_DefView (the icons). That empty WorkerW IS the wallpaper slot.
    ww = user32.FindWindowExW(progman, None, "WorkerW", None)
    if ww:
        return ww, "progman-child-workerw"

    # Classic layout: a top-level WorkerW hosts the icons; the wallpaper is its sibling.
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def _enum(hwnd, _l):
        if user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None):
            sib = user32.FindWindowExW(None, hwnd, "WorkerW", None)
            if sib:
                found.append(sib)
        return True

    user32.EnumWindows(_enum, 0)
    if found:
        return found[0], "workerw-sibling"
    # Last resort: parent straight into Progman.
    return progman, "progman"


def embed_by_title(title=TITLE):
    """Slot the window named `title` into the wallpaper layer, behind the desktop icons.
    Reusable so both this standalone script and jarvis_desktop.py share one code path."""
    hwnd = None
    for _ in range(40):  # wait for the window to actually exist
        hwnd = user32.FindWindowW(None, title)
        if hwnd:
            break
        time.sleep(0.1)
    if not hwnd:
        print("[wallpaper] couldn't find our window — is it open?", file=sys.stderr)
        return False

    target, layout = _wallpaper_target()

    # Become a child window (drop the top-level popup style) and parent into the layer.
    style = _getlong(hwnd, GWL_STYLE)
    _setlong(hwnd, GWL_STYLE, ((style & ~WS_POPUP) | WS_CHILD) & 0xFFFFFFFF)
    user32.SetParent(hwnd, target)

    # Fill the WorkerW (it already sits behind the icons, so no z-order push needed).
    w, h = _screen()
    user32.SetWindowPos(hwnd, HWND_TOP, 0, 0, w, h,
                        SWP_NOACTIVATE | SWP_SHOWWINDOW | SWP_FRAMECHANGED)

    ok = user32.GetParent(hwnd) == target
    print(f"[wallpaper] layout={layout} target={target} parented={ok}", file=sys.stderr)
    if ok:
        print("[wallpaper] JARVIS is now your desktop background.", file=sys.stderr)
    else:
        print("[wallpaper] embed didn't take — tell me and I'll try the next approach.",
              file=sys.stderr)
    return ok


def main():
    w, h = _screen()
    window = webview.create_window(
        TITLE, url=PAGE,
        frameless=True, on_top=False, resizable=False,
        width=w, height=h, x=0, y=0,
        background_color="#04070d",
    )
    window.events.shown += lambda: threading.Thread(
        target=embed_by_title, args=(TITLE,), daemon=True).start()
    webview.start()


if __name__ == "__main__":
    main()

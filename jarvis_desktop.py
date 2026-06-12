"""JARVIS — the desktop orb (true wallpaper element).

A dark space disc with the reactor + a ring of HUD icons, pinned into the actual
WALLPAPER layer (parented into the desktop's WorkerW). That means it behaves like the
wallpaper: it's ALWAYS there, it does NOT minimize on "show desktop" (Win+D / the
3-finger swipe), and your apps and icons sit on top of it. Your real wallpaper still
shows around the circular disc.

Because the wallpaper layer can't receive clicks (Windows sends them to the desktop),
the ring icons are visual — you drive JARVIS with global hotkeys (work from anywhere):

    Ctrl + Alt + V   →  start voice mode (talk to JARVIS)
    Ctrl + Alt + Q   →  quit JARVIS

Launch by double-clicking  JARVIS.vbs  (hidden + detached), or for testing:

    py jarvis_desktop.py
"""

import ctypes
from ctypes import wintypes
import math
import os
import queue
import random
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = 580
SPACE = "#05070e"
AMBER, CYAN, RED = "#ff9a2e", "#38e1ff", "#ff7a7a"
DARK, INK, FRAME = "#0a111c", "#ffd9a8", "#5c441f"
STAR_COLORS = ["#3a4658", "#566273", "#7d8ba0", "#aab8cc", "#dce8f5"]

PY_CONSOLE = os.path.join(sys.prefix, "Scripts", "python.exe")
CREATE_NEW_CONSOLE = 0x00000010

RINGS = [
    (0.92,  3, 0.26,  0.7, 3),
    (0.78, 20, 0.42, -1.1, 1),
    (0.60,  6, 0.14,  1.5, 2),
    (0.44, 34, 0.55, -1.8, 1),
]
BUTTONS = [
    ("voice",    "\U0001F399", AMBER),
    ("ask",      "\U0001F4AC", AMBER),
    ("youtube",  "▶",      AMBER),
    ("whatsapp", "WA",          CYAN),
    ("lock",     "\U0001F512", AMBER),
    ("saver",    "\U0001F50B", AMBER),
    ("off",      "⏻",      RED),
]

# ── Win32 plumbing (parent the orb into the wallpaper layer) ──────────────────
user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
for fn, res, args in [
    ("FindWindowW", wintypes.HWND, [wintypes.LPCWSTR, wintypes.LPCWSTR]),
    ("FindWindowExW", wintypes.HWND, [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]),
    ("GetAncestor", wintypes.HWND, [wintypes.HWND, wintypes.UINT]),
    ("SetParent", wintypes.HWND, [wintypes.HWND, wintypes.HWND]),
    ("GetParent", wintypes.HWND, [wintypes.HWND]),
    ("SetWindowRgn", ctypes.c_int, [wintypes.HWND, wintypes.HANDLE, wintypes.BOOL]),
]:
    f = getattr(user32, fn); f.restype = res; f.argtypes = args
gdi32.CreateEllipticRgn.restype = wintypes.HANDLE
_getlong = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
_setlong = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
_getlong.restype = ctypes.c_longlong; _getlong.argtypes = [wintypes.HWND, ctypes.c_int]
_setlong.restype = ctypes.c_longlong; _setlong.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_longlong]

GWL_STYLE, GA_ROOT, WS_CHILD, WS_POPUP = -16, 2, 0x40000000, 0x80000000
MOD_ALT, MOD_CONTROL, WM_HOTKEY = 0x0001, 0x0002, 0x0312
VK_V, VK_Q = 0x56, 0x51


def _wallpaper_target():
    """The window to parent into so the orb lives in the wallpaper layer (behind icons)."""
    progman = user32.FindWindowW("Progman", None)
    res = wintypes.DWORD()
    user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0x0000, 1000, ctypes.byref(res))
    ww = user32.FindWindowExW(progman, None, "WorkerW", None)  # new-Win11: WorkerW child of Progman
    return (ww or progman)


class Orb:
    def __init__(self, root):
        self.root = root
        self.cx = self.cy = SIZE / 2
        self.t = 0
        self.running = True
        self._brain = None
        self._lock = threading.Lock()
        self.hq = queue.Queue()

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.x, self.y = (sw - SIZE) // 2, (sh - SIZE) // 2
        root.geometry(f"{SIZE}x{SIZE}+{self.x}+{self.y}")
        root.overrideredirect(True)
        root.config(bg=SPACE)

        self.c = tk.Canvas(root, width=SIZE, height=SIZE, bg=SPACE, highlightthickness=0)
        self.c.pack()

        self._draw_backdrop()
        self.status = self.c.create_text(self.cx, self.cy, text="J A R V I S",
                                         fill=AMBER, font=("Consolas", 15, "bold"))
        self._build_buttons()
        self._animate()
        self.root.after(350, self._embed_wallpaper)   # slot into the wallpaper layer
        self.root.after(120, self._poll_hotkeys)       # listen for global hotkeys

    # ── dark space backdrop (drawn once) ──────────────────────────────────────
    def _draw_backdrop(self):
        Rd = SIZE / 2 - 4
        self.c.create_oval(self.cx - Rd, self.cy - Rd, self.cx + Rd, self.cy + Rd,
                           outline=FRAME, width=2, tags="bg")
        rng = random.Random(7)
        for _ in range(70):
            rr = math.sqrt(rng.random()) * (Rd - 12)
            a = rng.random() * math.tau
            x, y = self.cx + math.cos(a) * rr, self.cy + math.sin(a) * rr
            s = rng.choice([1, 1, 1, 2])
            self.c.create_oval(x - s, y - s, x + s, y + s,
                               fill=rng.choice(STAR_COLORS), outline="", tags="bg")

    def _build_buttons(self):
        R, n, rad = 232, len(BUTTONS), 26
        for i, (act, glyph, col) in enumerate(BUTTONS):
            ang = (i / n) * math.tau - math.pi / 2
            x, y = self.cx + math.cos(ang) * R, self.cy + math.sin(ang) * R
            self.c.create_oval(x - rad, y - rad, x + rad, y + rad,
                               fill=DARK, outline=col, width=2, tags="btn")
            font = ("Segoe UI Emoji", 15) if len(glyph) == 1 and ord(glyph) > 0x2000 else ("Consolas", 12, "bold")
            self.c.create_text(x, y, text=glyph, fill=col, font=font, tags="btn")

    # ── animation (cheap; small region, ~16 FPS) ──────────────────────────────
    def _animate(self):
        self.t += 1
        if self.running:
            self.c.delete("ring")
            for frac, segs, gap, spin, w in RINGS:
                r = frac * SIZE / 2
                box = (self.cx - r, self.cy - r, self.cx + r, self.cy + r)
                seg = 360 / segs
                rot = (self.t * spin) % 360
                for k in range(segs):
                    self.c.create_arc(*box, start=rot + k * seg, extent=seg * (1 - gap),
                                      style="arc", outline=AMBER, width=w, tags="ring")
            self.c.tag_raise("btn"); self.c.tag_raise(self.status)
        self.root.after(60, self._animate)

    # ── slot into the wallpaper layer, clipped to a circle ────────────────────
    def _embed_wallpaper(self):
        try:
            self.root.update_idletasks()
            hwnd = user32.GetAncestor(self.root.winfo_id(), GA_ROOT) or self.root.winfo_id()
            target = _wallpaper_target()
            style = _getlong(hwnd, GWL_STYLE)
            _setlong(hwnd, GWL_STYLE, ((style & ~WS_POPUP) | WS_CHILD) & 0xFFFFFFFF)
            user32.SetParent(hwnd, target)
            user32.MoveWindow(hwnd, self.x, self.y, SIZE, SIZE, True)
            user32.SetWindowRgn(hwnd, gdi32.CreateEllipticRgn(0, 0, SIZE, SIZE), True)
            ok = user32.GetParent(hwnd) == target
            print(f"[orb] pinned to wallpaper layer (target={target}, ok={ok})", flush=True)
        except Exception as e:
            print(f"[orb] wallpaper-pin failed: {e}", flush=True)

    # ── global hotkeys (dispatched on the Tk thread) ──────────────────────────
    def _poll_hotkeys(self):
        try:
            while True:
                act = self.hq.get_nowait()
                if act == "voice":
                    self.do_voice()
                elif act == "quit":
                    self.do_off()
        except queue.Empty:
            pass
        self.root.after(120, self._poll_hotkeys)

    # ── actions ────────────────────────────────────────────────────────────────
    def _orchestrator(self):
        if self._brain is None:
            with self._lock:
                if self._brain is None:
                    from agents.orchestrator import Orchestrator
                    self._brain = Orchestrator()
        return self._brain

    def do_voice(self):
        exe = PY_CONSOLE if os.path.exists(PY_CONSOLE) else "py"
        try:
            subprocess.Popen([exe, os.path.join(HERE, "jarvis_live.py"), "console"],
                             cwd=HERE, creationflags=CREATE_NEW_CONSOLE)
        except Exception as e:
            print(f"[orb] voice launch failed: {e}", flush=True)

    def do_off(self):
        self.root.destroy()
        os._exit(0)


def _hotkey_thread(q):
    """Register the global hotkeys and forward presses to the orb's queue."""
    u = ctypes.windll.user32
    u.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT, VK_V)
    u.RegisterHotKey(None, 2, MOD_CONTROL | MOD_ALT, VK_Q)
    msg = wintypes.MSG()
    while u.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        if msg.message == WM_HOTKEY:
            q.put({1: "voice", 2: "quit"}.get(msg.wParam))


def main():
    print("[orb] JARVIS is now part of your desktop. It won't minimize on 'show desktop'.", flush=True)
    print("[orb] Ctrl+Alt+V = voice   |   Ctrl+Alt+Q = quit", flush=True)
    root = tk.Tk()
    root.title("JARVIS-ORB")
    orb = Orb(root)
    threading.Thread(target=_hotkey_thread, args=(orb.hq,), daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    main()

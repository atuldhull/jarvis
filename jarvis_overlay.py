"""JARVIS — the clickable overlay for the holographic wallpaper.

A transparent, click-through layer that sits over the JARVIS wallpaper and puts a faint
button on each panel (and the globe). The empty space is fully click-through, so your
desktop and apps work normally — only the faint buttons capture clicks. Hover lights them
up; click runs a different action per panel.

    py jarvis_overlay.py        (run it after the wallpaper is set)

Buttons:  globe=Voice · GLOBAL FEED=Ask · POWER=Lock · WAVEFORM=Media · SATELLITE=Web ·
          TELEMETRY=WhatsApp · DIAGNOSTIC=System.    Ctrl+Alt+Q quits the overlay.
"""

import ctypes
from ctypes import wintypes
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser

import hud_layout as L

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
CHROMA = "#ff00ff"                          # transparent + click-through
CYAN, CYAN_HI, DIM = "#56c4ff", "#bfe9ff", "#2f5f74"
CHIP, CHIP_HI, DARK, INK = "#0a1c28", "#114660", "#0a131c", "#d8f4ff"

PY_CONSOLE = os.path.join(sys.prefix, "Scripts", "python.exe")
CREATE_NEW_CONSOLE = 0x00000010
MOD_ALT, MOD_CONTROL, WM_HOTKEY = 0x0001, 0x0002, 0x0312
VK_Q, VK_V = 0x51, 0x56


class Overlay:
    def __init__(self, root):
        self.root = root
        self._brain = None
        self._lock = threading.Lock()
        self.hq = queue.Queue()
        self._hide_after = None

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.fx, self.fy = sw / L.RENDER_W, sh / L.RENDER_H
        self.pinned = True            # keep sinking it under apps (desktop-only)
        root.geometry(f"{sw}x{sh}+0+0")
        root.overrideredirect(True)
        root.attributes("-transparentcolor", CHROMA)
        root.config(bg=CHROMA)
        self.c = tk.Canvas(root, width=sw, height=sh, bg=CHROMA, highlightthickness=0)
        self.c.pack()
        root.update_idletasks()
        self._make_desktop_widget()   # don't show in taskbar; survive 'show desktop'

        self.entry = tk.Entry(root, bg=DARK, fg=INK, insertbackground=CYAN, relief="flat",
                              justify="center", font=("Consolas", 13), width=34)
        self.entry.bind("<Return>", self._submit)
        self.entry.bind("<Escape>", lambda e: self._hide_ask())
        self.entry_win = self.c.create_window(sw // 2, int(sh * 0.5), window=self.entry, state="hidden")

        self._build()
        self.root.after(150, self._poll)
        self.root.after(700, self._sink)

    def _make_desktop_widget(self):
        """Toolwindow ex-style: no taskbar button, and NOT minimized by 'show desktop'."""
        try:
            u = ctypes.windll.user32
            hwnd = u.GetAncestor(self.root.winfo_id(), 2) or self.root.winfo_id()  # GA_ROOT
            GWL_EXSTYLE, WS_EX_TOOLWINDOW = -20, 0x00000080
            ex = u.GetWindowLongW(hwnd, GWL_EXSTYLE)
            u.SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_TOOLWINDOW)
        except Exception as e:
            print("[overlay] desktop-widget setup failed:", e, flush=True)

    def S(self, x, y):
        return x * self.fx, y * self.fy

    # ── faint button chips ────────────────────────────────────────────────────
    def _chip(self, cx, cy, label, action):
        w = max(78, len(label) * 11 + 26)
        h = 28
        tag = f"chip_{action}_{int(cx)}"
        r = self.c.create_rectangle(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2,
                                    fill=CHIP, outline="", tags=(tag,))
        t = self.c.create_text(cx, cy, text=label, fill=DIM, font=("Consolas", 11, "bold"), tags=(tag,))
        self.c.tag_bind(tag, "<Enter>", lambda e: (
            self.c.itemconfig(r, fill=CHIP_HI, outline=CYAN, width=1),
            self.c.itemconfig(t, fill=CYAN_HI), self.c.config(cursor="hand2")))
        self.c.tag_bind(tag, "<Leave>", lambda e: (
            self.c.itemconfig(r, fill=CHIP, outline=""),
            self.c.itemconfig(t, fill=DIM), self.c.config(cursor="")))
        self.c.tag_bind(tag, "<Button-1>", lambda e, a=action: self._do(a))

    def _build(self):
        for name, x, y, w, h, action, label in L.PANELS:
            cx, cy = self.S(x + w / 2, y + h - 16)
            self._chip(cx, cy, label, action)
        gx, gy, gr = L.GLOBE
        act, lab = L.GLOBE_ACTION
        cx, cy = self.S(gx, gy)
        self._chip(cx, cy, lab, act)
        # a small quit button, top-right
        self._chip(self.root.winfo_screenwidth() - 60, 34, "✕", "quit")

    # ── actions ────────────────────────────────────────────────────────────────
    def _do(self, action):
        getattr(self, f"act_{action}", lambda: None)()

    def _orchestrator(self):
        if self._brain is None:
            with self._lock:
                if self._brain is None:
                    from agents.orchestrator import Orchestrator
                    self._brain = Orchestrator()
        return self._brain

    def act_ask(self):
        self.pinned = False           # come forward so you can type
        self.c.itemconfig(self.entry_win, state="normal")
        self.root.lift(); self.root.focus_force()
        self.entry.delete(0, "end"); self.entry.focus_set()

    def _hide_ask(self):
        self.c.itemconfig(self.entry_win, state="hidden")
        self.pinned = True            # sink back under the apps
        try:
            self.root.lower()
        except Exception:
            pass

    def _submit(self, _e=None):
        text = self.entry.get().strip()
        self._hide_ask()
        if not text:
            return
        self._bubble("…")
        threading.Thread(target=self._ask_worker, args=(text,), daemon=True).start()

    def _ask_worker(self, text):
        try:
            reply = self._orchestrator().handle(text)
        except Exception as e:
            reply = f"I hit a snag, sir — {e}"
        self.root.after(0, lambda: self._bubble(reply))

    def _bubble(self, text):
        if self._hide_after:
            self.root.after_cancel(self._hide_after)
        self.c.delete("bubble")
        sw = self.root.winfo_screenwidth()
        t = self.c.create_text(sw // 2, int(self.root.winfo_screenheight() * 0.30), text=text,
                               fill=INK, width=540, justify="center", font=("Consolas", 12), tags="bubble")
        b = self.c.bbox(t)
        if b:
            r = self.c.create_rectangle(b[0] - 14, b[1] - 12, b[2] + 14, b[3] + 12,
                                        fill=DARK, outline=CYAN, tags="bubble")
            self.c.tag_lower(r, t)
        self._hide_after = self.root.after(min(15000, 4000 + len(text) * 45),
                                           lambda: self.c.delete("bubble"))

    def act_voice(self):
        exe = PY_CONSOLE if os.path.exists(PY_CONSOLE) else "py"
        try:
            subprocess.Popen([exe, os.path.join(HERE, "jarvis_live.py"), "console"],
                             cwd=HERE, creationflags=CREATE_NEW_CONSOLE)
            self._bubble("Voice mode is firing up, boss — talk to me.")
        except Exception as e:
            self._bubble(f"voice launch failed — {e}")

    def act_lock(self):     ctypes.windll.user32.LockWorkStation()
    def act_youtube(self):  webbrowser.open("https://www.youtube.com")
    def act_browser(self):  webbrowser.open("https://www.google.com")
    def act_whatsapp(self): webbrowser.open("https://web.whatsapp.com")
    def act_sysinfo(self):
        try:
            subprocess.Popen("taskmgr")
        except Exception:
            pass

    def act_quit(self):
        self.root.destroy()
        os._exit(0)

    # ── housekeeping ──────────────────────────────────────────────────────────
    def _sink(self):
        """Drop under the apps so the buttons show ONLY on the desktop, not over apps."""
        if self.pinned:
            try:
                self.root.lower()
            except Exception:
                pass
        self.root.after(1200, self._sink)

    def _poll(self):
        try:
            while True:
                act = self.hq.get_nowait()
                if act == "quit":
                    self.act_quit()
                elif act == "voice":
                    self.act_voice()
        except queue.Empty:
            pass
        self.root.after(150, self._poll)


def _hotkey_thread(q):
    u = ctypes.windll.user32
    u.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT, VK_Q)
    u.RegisterHotKey(None, 2, MOD_CONTROL | MOD_ALT, VK_V)
    msg = wintypes.MSG()
    while u.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        if msg.message == WM_HOTKEY:
            q.put({1: "quit", 2: "voice"}.get(msg.wParam))


def main():
    print("[overlay] JARVIS buttons active. Hover a panel's chip and click. Ctrl+Alt+Q quits.",
          flush=True)
    root = tk.Tk()
    root.title("JARVIS-OVERLAY")
    ov = Overlay(root)
    threading.Thread(target=_hotkey_thread, args=(ov.hq,), daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    main()

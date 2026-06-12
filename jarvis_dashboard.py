"""JARVIS — the dashboard (fullscreen command center).

A real, opaque, fullscreen UI (like Tony's): sidebar navigation, live system stats,
weather, voice, a JARVIS feed, and quick-command buttons — every one wired to a real
action. Rendered with pywebview; the brain is the same orchestrator everything uses.

    py jarvis_dashboard.py

The center portrait is a placeholder until you drop your photo at
assets/user.png (or .jpg) — then it shows you, in the JARVIS interface.
"""

import base64
import ctypes
from ctypes import wintypes
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

import webview

sys.stdout.reconfigure(encoding="utf-8")

try:
    import psutil
except ImportError:
    psutil = None

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "frontend", "dashboard.html")

# Optional centre portrait — drop any image at assets/user.png and it appears in the HUD.
USER_NAME = "STARK"
_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _photo_data_uri():
    """Read whatever local image the user placed and hand it to the page as a data URI
    (relative file paths don't load reliably in WebView2). Empty string if none."""
    for ext, mime in _MIME.items():
        f = os.path.join(HERE, "assets", "user" + ext)
        if os.path.exists(f):
            try:
                with open(f, "rb") as fh:
                    return f"data:{mime};base64," + base64.b64encode(fh.read()).decode()
            except Exception:
                return ""
    return ""

PY_CONSOLE = os.path.join(sys.prefix, "Scripts", "python.exe")
CREATE_NEW_CONSOLE = 0x00000010


def _run(*cmd):
    try:
        subprocess.Popen(cmd, cwd=HERE)
    except Exception as e:
        print("[dashboard] launch failed:", cmd, e, file=sys.stderr)


class JarvisAPI:
    def __init__(self):
        self._brain = None
        self._lock = threading.Lock()
        self._net0 = None
        self._weather = None
        self._window = None

    def attach(self, window):
        self._window = window

    def _orchestrator(self):
        if self._brain is None:
            with self._lock:
                if self._brain is None:
                    from agents.orchestrator import Orchestrator
                    self._brain = Orchestrator()
        return self._brain

    # ── data feeds ────────────────────────────────────────────────────────────
    def info(self):
        osname = "Windows"
        try:
            import platform
            osname = platform.system() + " " + platform.release()
        except Exception:
            pass
        return {"user": USER_NAME, "version": "v6.2.1", "os": osname, "photo": _photo_data_uri()}

    def stats(self):
        if not psutil:
            return {"cpu": 0, "ram": 0, "disk": 0, "net": 0, "battery": None,
                    "plugged": False, "uptime": "00:00:00", "optimal": 100}
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        try:
            disk = psutil.disk_usage(os.path.abspath(os.sep)).percent
        except Exception:
            disk = 0
        now = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
        net = 0
        if self._net0 is not None:
            net = max(0, (now - self._net0)) / 1024  # KB since last poll
        self._net0 = now
        bat = psutil.sensors_battery()
        up = int(time.time() - psutil.boot_time())
        optimal = max(0, min(100, int(100 - (cpu * 0.4 + ram * 0.4 + disk * 0.2))))
        return {
            "cpu": round(cpu), "ram": round(ram), "disk": round(disk), "net": round(net),
            "battery": (round(bat.percent) if bat else None),
            "plugged": (bool(bat.power_plugged) if bat else False),
            "uptime": f"{up // 3600:02d}:{(up % 3600) // 60:02d}:{up % 60:02d}",
            "optimal": optimal,
        }

    def weather(self, refresh=False):
        if self._weather and not refresh:
            return self._weather
        try:
            req = urllib.request.Request("https://wttr.in/?format=j1",
                                         headers={"User-Agent": "curl/8"})
            data = json.loads(urllib.request.urlopen(req, timeout=6).read().decode())
            cur = data["current_condition"][0]
            days = []
            for d in data["weather"][:4]:
                days.append({"date": d["date"], "max": d["maxtempC"], "min": d["mintempC"]})
            area = data.get("nearest_area", [{}])[0]
            city = (area.get("areaName", [{}])[0].get("value", "")) if area else ""
            self._weather = {
                "temp": cur["temp_C"], "desc": cur["weatherDesc"][0]["value"],
                "feels": cur["FeelsLikeC"], "humidity": cur["humidity"],
                "wind": cur["windspeedKmph"], "city": city, "days": days,
            }
        except Exception as e:
            self._weather = {"temp": "--", "desc": "offline", "feels": "--",
                             "humidity": "--", "wind": "--", "city": "", "days": []}
        return self._weather

    # ── actions (each button) ──────────────────────────────────────────────────
    def ask(self, text):
        text = (text or "").strip()
        if not text:
            return ""
        try:
            return self._orchestrator().handle(text)
        except Exception as e:
            return f"I hit a snag, sir — {e}"

    def voice(self):
        exe = PY_CONSOLE if os.path.exists(PY_CONSOLE) else "py"
        try:
            subprocess.Popen([exe, os.path.join(HERE, "jarvis_live.py"), "console"],
                             cwd=HERE, creationflags=CREATE_NEW_CONSOLE)
        except Exception as e:
            print("[dashboard] voice failed:", e, file=sys.stderr)
        return True

    def action(self, name):
        """Dispatch a named UI action. Returns a short status string for the feed."""
        try:
            if name == "web":          webbrowser.open("https://www.google.com")
            elif name == "files":      _run("explorer")
            elif name == "media":      webbrowser.open("https://www.youtube.com")
            elif name == "tools":      _run("taskmgr")
            elif name == "security":   _run("cmd", "/c", "start", "windowsdefender:")
            elif name == "settings":   _run("cmd", "/c", "start", "ms-settings:")
            elif name == "notes":      _run("notepad")
            elif name == "calculator": _run("calc")
            elif name == "cleanup":    _run("cleanmgr")
            elif name == "music":      webbrowser.open("https://music.youtube.com")
            elif name == "screenshot": return self._screenshot()
            elif name == "lock":       ctypes.windll.user32.LockWorkStation()
            else:                      return f"unknown action: {name}"
        except Exception as e:
            return f"{name} failed: {e}"
        return f"{name} done"

    def _screenshot(self):
        try:
            from PIL import ImageGrab
            folder = os.path.join(HERE, "assets", "shots")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f"shot_{int(time.time())}.png")
            ImageGrab.grab().save(path)
            return "screenshot saved"
        except Exception as e:
            return f"screenshot failed: {e}"

    def quit(self):
        try:
            for w in list(webview.windows):
                w.destroy()
        except Exception:
            pass
        os._exit(0)


WIN_TITLE = "JARVIS-DASHBOARD"
_dwm = ctypes.windll.dwmapi


def _cloaked(hwnd):
    """True if 'show desktop' DWM-cloaked the window (hidden without minimizing)."""
    v = ctypes.c_int(0)
    try:
        if _dwm.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(v), ctypes.sizeof(v)) == 0:
            return v.value != 0
    except Exception:
        pass
    return False


def _pin_persistent():
    """Bind the dashboard INTO the desktop (Rainmeter-style): re-parent it onto Progman,
    above the icons. Then 'show desktop' / the 3-finger swipe can't hide it — it's part of
    the desktop now, so the swipe only reveals it. Closing JARVIS destroys the window, so
    your normal wallpaper + icons come right back."""
    u = ctypes.windll.user32
    u.FindWindowW.restype = wintypes.HWND
    u.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    u.SetParent.restype = wintypes.HWND
    u.SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
    getlong = getattr(u, "GetWindowLongPtrW", u.GetWindowLongW)
    setlong = getattr(u, "SetWindowLongPtrW", u.SetWindowLongW)
    getlong.restype = ctypes.c_longlong
    getlong.argtypes = [wintypes.HWND, ctypes.c_int]
    setlong.restype = ctypes.c_longlong
    setlong.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_longlong]

    hwnd = None
    for _ in range(60):
        hwnd = u.FindWindowW(None, WIN_TITLE)
        if hwnd:
            break
        time.sleep(0.1)
    if not hwnd:
        print("[dashboard] pin: window not found", file=sys.stderr)
        return

    progman = u.FindWindowW("Progman", None)
    GWL_STYLE, WS_CHILD, WS_POPUP = -16, 0x40000000, 0x80000000
    HWND_TOP, SWP_SHOWWINDOW = 0, 0x0040
    sw, sh = u.GetSystemMetrics(0), u.GetSystemMetrics(1)

    style = getlong(hwnd, GWL_STYLE)
    setlong(hwnd, GWL_STYLE, ((style & ~WS_POPUP) | WS_CHILD) & 0xFFFFFFFF)
    u.SetParent(hwnd, progman)
    u.SetWindowPos(hwnd, HWND_TOP, 0, 0, sw, sh, SWP_SHOWWINDOW)
    print("[dashboard] bound to the desktop — the swipe can't hide it now.", file=sys.stderr)

    while True:                                    # keep it filling the desktop
        try:
            rc = wintypes.RECT()
            u.GetWindowRect(hwnd, ctypes.byref(rc))
            if (rc.right - rc.left, rc.bottom - rc.top) != (sw, sh):
                u.SetWindowPos(hwnd, HWND_TOP, 0, 0, sw, sh, SWP_SHOWWINDOW)
        except Exception:
            pass
        time.sleep(0.5)


def main():
    api = JarvisAPI()
    u = ctypes.windll.user32
    sw, sh = u.GetSystemMetrics(0), u.GetSystemMetrics(1)
    window = webview.create_window(
        WIN_TITLE, url=PAGE, js_api=api,
        frameless=True, easy_drag=False, width=sw, height=sh, x=0, y=0,
        background_color="#04070e",
    )
    api.attach(window)
    window.events.shown += lambda: threading.Thread(target=_pin_persistent, daemon=True).start()
    webview.start()


if __name__ == "__main__":
    main()

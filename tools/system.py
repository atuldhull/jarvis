"""System tools — talk to the computer itself: the time, and launching apps."""

import datetime
import platform
import subprocess

from .registry import tool


@tool("get_time", "Get the current local date and time.")
def get_time():
    return datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p")


@tool("get_system_info", "Report basic system info: OS, machine, and Python version.")
def get_system_info():
    return (
        f"{platform.system()} {platform.release()} ({platform.machine()}); "
        f"Python {platform.python_version()}"
    )


# Friendly names mapped to their Windows executables. Unknown names are passed
# straight to `start`, which resolves most installed apps.
_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",
    "files": "explorer.exe",
    "browser": "msedge.exe",
    "edge": "msedge.exe",
    "chrome": "chrome.exe",
    "settings": "ms-settings:",
}


@tool(
    "open_app",
    "Open a desktop application by name, e.g. notepad, calculator, paint, browser, settings.",
    {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "The app to open, e.g. 'notepad'."}
        },
        "required": ["name"],
    },
)
def open_app(name):
    exe = _APPS.get(name.strip().lower(), name)
    try:
        # `start "" <exe>` launches the app and returns immediately.
        subprocess.Popen(["cmd", "/c", "start", "", exe])
        return f"Opened {name}."
    except Exception as e:
        return f"Could not open {name}: {e}"

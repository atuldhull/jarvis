"""System tools — talk to the computer itself: the time, launching apps, and power."""

import datetime
import platform
import subprocess

import config

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


# ── Power control ─────────────────────────────────────────────────────────────
# Lock/sleep are harmless and instant. Shutdown/restart are gated by confirm=True
# (the safety layer asks first) AND fire after a short, cancellable delay.

@tool("lock_screen", "Lock the Windows screen right now (the password is needed to get back in).")
def lock_screen():
    subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
    return "Locked the screen."


@tool("sleep_pc", "Put the computer to sleep (suspends; resumes where you left off).")
def sleep_pc():
    # SetSuspendState: sleeps now (hibernates instead if hibernation is enabled).
    subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
    return "Going to sleep, sir."


@tool(
    "shutdown_pc",
    "Shut down / power off the computer. Fires after a short, cancellable delay.",
    {
        "type": "object",
        "properties": {
            "seconds": {"type": "integer", "description": "Delay before powering off; omit for the default."}
        },
    },
    confirm=True,
)
def shutdown_pc(seconds=None):
    delay = config.SHUTDOWN_DELAY if seconds is None else int(seconds)
    subprocess.Popen(["shutdown", "/s", "/t", str(delay)])
    return f"Shutting down in {delay}s. Say 'cancel shutdown' to stop it."


@tool(
    "restart_pc",
    "Restart / reboot the computer. Fires after a short, cancellable delay.",
    {
        "type": "object",
        "properties": {
            "seconds": {"type": "integer", "description": "Delay before rebooting; omit for the default."}
        },
    },
    confirm=True,
)
def restart_pc(seconds=None):
    delay = config.SHUTDOWN_DELAY if seconds is None else int(seconds)
    subprocess.Popen(["shutdown", "/r", "/t", str(delay)])
    return f"Restarting in {delay}s. Say 'cancel shutdown' to stop it."


@tool("cancel_shutdown", "Abort a shutdown or restart that's counting down.")
def cancel_shutdown():
    r = subprocess.run(["shutdown", "/a"], capture_output=True, text=True)
    return "Cancelled the shutdown." if r.returncode == 0 else "Nothing was scheduled to cancel."

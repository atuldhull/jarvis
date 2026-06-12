"""Shared HUD layout — panel positions in the wallpaper's 1920x1080 render space.
Both the wallpaper (make_wallpaper.py) and the clickable overlay (jarvis_overlay.py)
read these so the faint buttons line up exactly on top of the painted panels.
"""

RENDER_W, RENDER_H = 1920, 1080
GLOBE = (960, 470, 215)            # cx, cy, r

# name, x, y, w, h, action, button-label
PANELS = [
    ("GLOBAL FEED",    70, 130, 360, 215, "ask",      "ASK"),
    ("POWER OUTPUT",   95, 380, 305, 180, "lock",     "LOCK"),
    ("WAVEFORM",       60, 600, 270, 150, "youtube",  "MEDIA"),
    ("SATELLITE GRID", 1490, 130, 365, 205, "browser", "WEB"),
    ("TELEMETRY",      1535, 370, 305, 175, "whatsapp", "CHAT"),
    ("DIAGNOSTIC",     1560, 585, 280, 155, "sysinfo",  "SYS"),
]
GLOBE_ACTION = ("voice", "VOICE")   # the globe itself = talk to JARVIS

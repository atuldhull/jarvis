"""Generate a JARVIS holographic-interface wallpaper — Tony-Stark-workshop style: many
translucent blue HUD panels (charts, readouts, gauges, a wireframe globe) floating in dark
space with light flares. Renders a PNG; --set also makes it your Windows wallpaper.

    py make_wallpaper.py          # build assets/jarvis_wallpaper.png
    py make_wallpaper.py --set    # build it AND set it as the desktop wallpaper
"""

import ctypes
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "jarvis_wallpaper.png")
W, H = 1920, 1080

CYAN = (86, 196, 255)
CYAN_HI = (200, 238, 255)
AMBER = (255, 176, 80)

FT_T = FT_S = None  # fonts, loaded in build()


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def lerp(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def glow(cx, cy, r, color, alpha, blur):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (alpha,))
    return g.filter(ImageFilter.GaussianBlur(blur))


# ── panel content painters (draw inside the panel) ───────────────────────────
def c_text(d, w, h, acc, dep):
    rng = random.Random(w * 7 + h)
    y = 38
    while y < h - 14:
        ln = rng.randint(int((w - 28) * 0.35), w - 28)
        a = 150 if rng.random() < 0.12 else 70
        d.line([14, y, 14 + ln, y], fill=acc + (int(a * dep),), width=2)
        y += 11


def c_bars(d, w, h, acc, dep):
    x0, y1, x1 = 14, h - 14, w - 14
    rng = random.Random(w + h * 3)
    n = 11
    bw = (x1 - x0) / n
    for i in range(n):
        bh = (h - 52) * (0.18 + 0.82 * rng.random())
        d.rectangle([x0 + i * bw + 2, y1 - bh, x0 + i * bw + bw - 3, y1], fill=acc + (int(150 * dep),))


def c_line(d, w, h, acc, dep):
    x0, y0, x1, y1 = 14, 38, w - 14, h - 14
    for gy in range(4):
        yy = y0 + (y1 - y0) * gy / 3
        d.line([x0, yy, x1, yy], fill=acc + (int(28 * dep),))
    rng = random.Random(w * 2 + h)
    n = 18
    pts = [(x0 + (x1 - x0) * i / (n - 1), y1 - (y1 - y0) * (0.15 + 0.75 * rng.random())) for i in range(n)]
    d.line(pts, fill=acc + (int(210 * dep),), width=2)


def c_wave(d, w, h, acc, dep):
    x0, x1 = 14, w - 14
    mid = (38 + h - 14) / 2
    amp = (h - 56) / 2.3
    pts = [(x0 + (x1 - x0) * i / 140, mid + math.sin(i / 7) * amp * (0.45 + 0.55 * math.sin(i / 38)))
           for i in range(141)]
    d.line(pts, fill=acc + (int(210 * dep),), width=2)


def c_rings(d, w, h, acc, dep):
    cx, cy = w / 2, (38 + h) / 2
    r = min(w, h - 38) / 2 - 10
    for rr, s, e in [(r, 20, 320), (r * 0.7, 200, 150), (r * 0.42, 0, 360)]:
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], s, e, fill=acc + (int(200 * dep),), width=2)


def c_grid(d, w, h, acc, dep):
    x0, y0, x1, y1 = 14, 38, w - 14, h - 14
    for gx in range(7):
        d.line([x0 + (x1 - x0) * gx / 6, y0, x0 + (x1 - x0) * gx / 6, y1], fill=acc + (int(45 * dep),))
    for gy in range(5):
        d.line([x0, y0 + (y1 - y0) * gy / 4, x1, y0 + (y1 - y0) * gy / 4], fill=acc + (int(45 * dep),))
    d.rectangle([x0 + (x1 - x0) * 2 / 6, y0 + (y1 - y0) / 4, x0 + (x1 - x0) * 3 / 6, y0 + (y1 - y0) / 2],
                outline=acc + (int(210 * dep),), width=2)


# ── a floating holographic panel ─────────────────────────────────────────────
def panel(base, x, y, w, h, title, content, acc=CYAN, dep=1.0):
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=9,
                        fill=acc + (int(22 * dep),), outline=acc + (int(170 * dep),), width=2)
    if title:
        d.text((12, 8), title, font=FT_T, fill=CYAN_HI + (int(220 * dep),))
        d.line([12, 29, w - 12, 29], fill=acc + (int(90 * dep),))
    for yy in range(33, h - 4, 4):                       # hologram scanlines
        d.line([6, yy, w - 6, yy], fill=acc + (int(11 * dep),))
    for cxx, cyy, sx, sy in [(5, 5, 1, 1), (w - 5, 5, -1, 1), (5, h - 5, 1, -1), (w - 5, h - 5, -1, -1)]:
        d.line([cxx, cyy, cxx + 11 * sx, cyy], fill=CYAN_HI + (int(220 * dep),), width=2)
        d.line([cxx, cyy, cxx, cyy + 11 * sy], fill=CYAN_HI + (int(220 * dep),), width=2)
    if content:
        content(d, w, h, acc, dep)
    if dep < 0.6:
        lay = lay.filter(ImageFilter.GaussianBlur(1.1))  # far panels go soft (depth)
    base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(6)), (x, y))  # bloom
    base.alpha_composite(lay, (x, y))


def globe(base, cx, cy, r):
    base.alpha_composite(glow(cx, cy, int(r * 1.4), CYAN, 58, 65))
    base.alpha_composite(glow(cx, cy, int(r * 0.55), CYAN_HI, 34, 44))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=CYAN_HI + (235,), width=2)
    for lat in (-62, -38, -13, 13, 38, 62):              # latitude lines
        rad = math.radians(lat)
        yy = cy - r * math.sin(rad)
        rx = r * math.cos(rad)
        ry = max(3, rx * 0.17)
        d.ellipse([cx - rx, yy - ry, cx + rx, yy + ry], outline=CYAN + (120,))
    for k in range(6):                                   # longitude lines
        rx = abs(r * math.cos(k * math.pi / 6))
        d.ellipse([cx - rx, cy - r, cx + rx, cy + r], outline=CYAN + (105,))
    # tilted orbit ring + travelling dots
    d.ellipse([cx - r * 1.5, cy - r * 0.42, cx + r * 1.5, cy + r * 0.42], outline=AMBER + (130,), width=1)
    for t in (25, 215):
        ox, oy = cx + 1.5 * r * math.cos(math.radians(t)), cy + 0.42 * r * math.sin(math.radians(t))
        d.ellipse([ox - 4, oy - 4, ox + 4, oy + 4], fill=AMBER + (220,))
    # HUD reticle ring framing the globe
    R2 = r * 1.46
    seg = 360 / 3
    for k in range(3):
        d.arc([cx - R2, cy - R2, cx + R2, cy + R2], 20 + k * seg, 20 + k * seg + seg * 0.82,
              fill=CYAN + (160,), width=2)
    for k in range(48):
        a = math.radians(k * 7.5)
        r1, r2 = R2 + 6, R2 + (18 if k % 4 == 0 else 12)
        d.line([cx + math.cos(a) * r1, cy + math.sin(a) * r1,
                cx + math.cos(a) * r2, cy + math.sin(a) * r2], fill=CYAN + (120,))
    base.alpha_composite(lay)


def mini_gauge(base, cx, cy, r, dep=0.5):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for rr, s, e in [(r, 0, 270), (r * 0.6, 180, 120)]:
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], s, e, fill=CYAN + (int(160 * dep),), width=2)
    base.alpha_composite(lay)


def streaks(base):
    base.alpha_composite(glow(W // 2, H - 30, 620, CYAN, 60, 150))   # desk light bloom
    base.alpha_composite(glow(W // 2 - 360, H - 70, 260, CYAN_HI, 40, 90))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for yy, al, wd in [(H - 96, 60, 1), (H - 70, 150, 2), (H - 52, 90, 1)]:
        d.line([120, yy, W - 120, yy], fill=CYAN_HI + (al,), width=wd)
    base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1)))


def background():
    img = Image.new("RGB", (W, H), (2, 4, 9))
    d = ImageDraw.Draw(img)
    inner, outer = (10, 20, 34), (2, 4, 9)
    cx, cy, R = W // 2, int(H * 0.62), 1300
    for i in range(120, 0, -1):
        t = i / 120
        r = R * t
        d.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=lerp(inner, outer, 1 - t))
    return img.convert("RGBA")


def build():
    global FT_T, FT_S
    FT_T = font("C:/Windows/Fonts/consola.ttf", 15)
    FT_S = font("C:/Windows/Fonts/consola.ttf", 12)

    img = background()
    # faint far panels first (depth)
    panel(img, 470, 175, 215, 120, "", c_line, dep=0.45)
    panel(img, 1245, 200, 210, 120, "", c_bars, dep=0.45)
    panel(img, 430, 660, 190, 110, "", c_grid, dep=0.42)
    panel(img, 1300, 660, 200, 110, "", c_wave, dep=0.42)

    mini_gauge(img, 700, 690, 46, dep=0.5)
    mini_gauge(img, 1230, 700, 40, dep=0.5)
    mini_gauge(img, 760, 250, 34, dep=0.45)
    globe(img, W // 2, 470, 215)

    # near hero panels — left cluster
    panel(img, 70, 130, 360, 215, "GLOBAL FEED", c_text)
    panel(img, 95, 380, 305, 180, "POWER OUTPUT", c_bars, acc=AMBER)
    panel(img, 60, 600, 270, 150, "WAVEFORM", c_wave)
    # right cluster
    panel(img, 1490, 130, 365, 205, "SATELLITE GRID", c_grid)
    panel(img, 1535, 370, 305, 175, "TELEMETRY", c_line)
    panel(img, 1560, 585, 280, 155, "DIAGNOSTIC", c_rings, acc=AMBER)

    streaks(img)

    d = ImageDraw.Draw(img)
    title = "J . A . R . V . I . S"
    bb = d.textbbox((0, 0), title, font=FT_T)
    d.text((W / 2 - (bb[2] - bb[0]) / 2, 40), title, font=FT_T, fill=CYAN_HI + (220,))
    d.text((W / 2 - 96, 740), "JUST A RATHER VERY INTELLIGENT SYSTEM", font=FT_S, fill=CYAN + (150,))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.convert("RGB").save(OUT, "PNG")
    print("wrote", OUT)
    return OUT


def set_wallpaper(path):
    SPI_SETDESKWALLPAPER, SPIF = 0x0014, 0x01 | 0x02
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, os.path.abspath(path), SPIF)
    print("wallpaper set.")


if __name__ == "__main__":
    p = build()
    if "--set" in sys.argv:
        set_wallpaper(p)

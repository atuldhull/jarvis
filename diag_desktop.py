"""Probe the desktop's window structure (no GUI) so we embed the wallpaper correctly.
Walks Progman's direct children in z-order and looks for a WorkerW to render into."""
import ctypes
from ctypes import wintypes

u = ctypes.windll.user32
u.FindWindowW.restype = wintypes.HWND
u.FindWindowExW.restype = wintypes.HWND
u.FindWindowExW.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
u.GetWindow.restype = wintypes.HWND
u.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]

GW_CHILD, GW_HWNDNEXT = 5, 2


def cls(hwnd):
    b = ctypes.create_unicode_buffer(256)
    u.GetClassNameW(hwnd, b, 256)
    return b.value


def rect(hwnd):
    r = wintypes.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)


def children(parent):
    out, c = [], u.GetWindow(parent, GW_CHILD)
    while c:
        out.append(c)
        c = u.GetWindow(c, GW_HWNDNEXT)
    return out


progman = u.FindWindowW("Progman", None)
print("Progman:", progman)

res = wintypes.DWORD()
u.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0x0000, 1000, ctypes.byref(res))

print("\nDirect children of Progman (z-order: first = TOP, last = BOTTOM):")
for c in children(progman):
    print(f"  {cls(c):24s} hwnd={c:<10} rect={rect(c)}")

ww = u.FindWindowExW(progman, None, "WorkerW", None)
print("\nWorkerW that is a CHILD of Progman:", ww)
if ww:
    print("  its children:", [(cls(x), x) for x in children(ww)])

# Also: is there a top-level WorkerW whose child is SHELLDLL_DefView?
print("\nTop-level WorkerW hosting icons:")
WNDENUM = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
def _enum(hwnd, _l):
    if cls(hwnd) == "WorkerW" and u.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None):
        print(f"  WorkerW {hwnd} hosts SHELLDLL_DefView")
    return True
u.EnumWindows(WNDENUM(_enum), 0)
print("probe done")

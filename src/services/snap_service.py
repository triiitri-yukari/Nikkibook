"""
Snap automation service for NikkiBook.
Automates the screenshot + share-link capture workflow from the Infinity Nikki game.

Uses OpenCV template matching to find UI buttons and pyautogui to control the mouse.
"""
import time
import ctypes
import io
from pathlib import Path
from typing import Callable, Optional, Tuple

import cv2
import numpy as np
import pyautogui

# Set DPI awareness BEFORE any screenshot is taken.
# Without this, pyautogui screenshots may be scaled incorrectly on high-DPI displays,
# causing template matching to fail entirely.
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from ..config import ASSETS_CLICKER_DIR


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SnapError(Exception):
    """Raised when a step in the snap workflow fails."""
    def __init__(self, step: int, message: str):
        self.step = step
        super().__init__(f"Step {step} failed: {message}")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOTAL_STEPS = 10

# Template matching  (edge / outline based)
MATCH_CONFIDENCE = 0.65       # Minimum edge-match score to accept
SCALE_MIN = 0.5               # Smallest template scale factor
SCALE_MAX = 2.0               # Largest template scale factor
SCALE_STEPS = 30              # Number of scale factors to try

# Canny edge-detection thresholds
CANNY_LOW  = 50
CANNY_HIGH = 150

# pyautogui safety settings
pyautogui.FAILSAFE = True     # Move mouse to corner to abort
pyautogui.PAUSE = 0.3         # Small pause between actions


# ---------------------------------------------------------------------------
# Window management
# ---------------------------------------------------------------------------

def _find_game_window() -> Optional[int]:
    """
    Find the Infinity Nikki game window by title.
    Searches for '无限暖暖', 'InfinityNikki', and 'Infinity Nikki'.

    Returns the window handle (HWND) if found, None otherwise.
    """
    if not HAS_WIN32:
        return None

    target_titles = ['无限暖暖', 'InfinityNikki', 'Infinity Nikki']
    found_hwnd = None

    def enum_callback(hwnd, _):
        nonlocal found_hwnd
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            for target in target_titles:
                if target.lower() in title.lower():
                    found_hwnd = hwnd
                    return False  # Stop enumeration
        return True

    try:
        win32gui.EnumWindows(enum_callback, None)
    except Exception:
        pass  # EnumWindows raises when callback returns False

    return found_hwnd


def _focus_game_window() -> None:
    """
    Bring the Infinity Nikki game window to the foreground.

    Raises SnapError if the game window cannot be found.
    """
    hwnd = _find_game_window()
    if hwnd is None:
        raise SnapError(1, "Cannot find Infinity Nikki game window. "
                         "Make sure the game is running (无限暖暖 or InfinityNikki).")

    try:
        # Restore if minimised
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        # Bring to foreground
        ctypes.windll.user32.AllowSetForegroundWindow(
            ctypes.windll.kernel32.GetCurrentProcessId()
        )
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
    except Exception as e:
        raise SnapError(1, f"Failed to focus game window: {e}")


# ---------------------------------------------------------------------------
# Image recognition helpers
# ---------------------------------------------------------------------------

def _load_template(name: str) -> np.ndarray:
    """Load a template image from the assets-clicker directory (BGR)."""
    path = ASSETS_CLICKER_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Template image not found: {path}")

    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Failed to decode template image: {path}")
    return img


def _screenshot_bgr() -> np.ndarray:
    """Take a full-screen screenshot and return it as a BGR numpy array."""
    pil = pyautogui.screenshot()
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def _to_edges(img: np.ndarray) -> np.ndarray:
    """
    Convert a BGR image to a Canny edge map.

    This makes matching background-agnostic: only the *outline* of the
    UI element is compared, not its colour fill.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Canny(gray, CANNY_LOW, CANNY_HIGH)


def _find_template(template_name: str,
                   confidence: float = MATCH_CONFIDENCE
                   ) -> Optional[Tuple[int, int, int, int]]:
    """
    Multi-scale **edge-based** template match.

    Both the screen capture and the template are converted to Canny edge
    images before matching.  This makes detection robust against varying
    in-game backgrounds and colour themes — only the shape/outline of the
    UI element matters.

    Returns (x, y, w, h) of the best match or None if below *confidence*.
    """
    template = _load_template(template_name)
    screen   = _screenshot_bgr()

    # Convert to edge maps
    template_edges = _to_edges(template)
    screen_edges   = _to_edges(screen)

    t_h, t_w = template_edges.shape[:2]
    s_h, s_w = screen_edges.shape[:2]

    scales = np.linspace(SCALE_MIN, SCALE_MAX, SCALE_STEPS)
    best_val   = -1.0
    best_loc   = None
    best_scale = 1.0

    for scale in scales:
        new_w = int(t_w * scale)
        new_h = int(t_h * scale)

        if new_w < 10 or new_h < 10:
            continue
        if new_w >= s_w or new_h >= s_h:
            continue

        resized = cv2.resize(template_edges, (new_w, new_h),
                             interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(screen_edges, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best_val:
            best_val   = max_val
            best_loc   = max_loc
            best_scale = scale

    if best_val < confidence or best_loc is None:
        return None

    matched_w = int(t_w * best_scale)
    matched_h = int(t_h * best_scale)
    return (best_loc[0], best_loc[1], matched_w, matched_h)


def _find_and_click(template_name: str,
                    step: int,
                    description: str,
                    timeout: float = 10.0,
                    retry_interval: float = 2.0,
                    confidence: float = MATCH_CONFIDENCE
                    ) -> Tuple[int, int, int, int]:
    """
    Repeatedly search for *template_name* on screen and click its centre.

    Retries every *retry_interval* seconds until *timeout* is reached.
    Raises SnapError if the template is never found.
    """
    start = time.time()

    while True:
        match = _find_template(template_name, confidence)
        if match is not None:
            x, y, w, h = match
            pyautogui.click(x + w // 2, y + h // 2)
            return match

        if time.time() - start >= timeout:
            raise SnapError(step,
                            f"Could not find '{description}' on screen "
                            f"after {timeout:.0f}s. "
                            f"Make sure the game UI is visible.")
        time.sleep(retry_interval)


def _capture_cropped_screenshot(template_name: str,
                                step: int,
                                width: int = 1135,
                                height: int = 635,
                                offset_x: int = 0,
                                offset_y: int = 0
                                ) -> bytes:
    """
    Locate *template_name*, use its **bottom-right corner** as anchor,
    and capture a *width*×*height* region extending left and up.
    
    offset_x and offset_y allow shifting the anchor point left and up.

    Returns PNG bytes.
    """
    match = _find_template(template_name)
    if match is None:
        raise SnapError(step, "Could not find crop reference icon on screen.")

    x, y, w, h = match
    anchor_x = x + w - offset_x   # bottom-right x (shifted)
    anchor_y = y + h - offset_y   # bottom-right y (shifted)

    cap_x = max(0, anchor_x - width)
    cap_y = max(0, anchor_y - height)

    pil = pyautogui.screenshot(region=(cap_x, cap_y, width, height))
    buf = io.BytesIO()
    pil.save(buf, format='PNG')
    return buf.getvalue()


def _read_clipboard() -> str:
    """Read Unicode text from the Windows clipboard."""
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            return win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        except TypeError:
            try:
                raw = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                return raw.decode('utf-8', errors='replace') if isinstance(raw, bytes) else str(raw)
            except Exception:
                return ""
        finally:
            win32clipboard.CloseClipboard()
    except Exception:
        # Fallback: PowerShell Get-Clipboard
        try:
            import subprocess
            result = subprocess.run(
                ['powershell', '-command', 'Get-Clipboard'],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return ""


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

def run_snap_workflow(
    progress_callback: Optional[Callable[[int, str], None]] = None,
    hide_ui_callback: Optional[Callable[[], None]] = None,
    show_ui_callback: Optional[Callable[[], None]] = None,
    skip_album: bool = False,
    capture_area: str = "full",
) -> Tuple[bytes, str]:
    """
    Execute the full snap workflow.

    Returns (screenshot_png_bytes, share_link_text).
    Raises SnapError if any step fails.
    """

    def report(step: int, msg: str):
        if progress_callback:
            progress_callback(step, msg)

    def hide_ui():
        if hide_ui_callback:
            hide_ui_callback()
        time.sleep(0.3)

    def show_ui():
        if show_ui_callback:
            show_ui_callback()

    # ------------------------------------------------------------------
    # Step 1  –  Navigate to game window
    # ------------------------------------------------------------------
    report(1, "Focusing Infinity Nikki window…")
    _focus_game_window()
    time.sleep(0.5)

    # ------------------------------------------------------------------
    # Step 2  –  Find & click 'share' button
    # ------------------------------------------------------------------
    report(2, "Looking for Share button…")
    _find_and_click("share.png", step=2, description="Share button")

    # ------------------------------------------------------------------
    # Step 3  –  Pause 2 seconds
    # ------------------------------------------------------------------
    report(3, "Waiting for share panel…")
    time.sleep(2)

    # ------------------------------------------------------------------
    # Step 4  –  Capture cropped screenshot using cropicon anchor
    #            Hide the NikkiBook dialog so it doesn't appear in the shot
    # ------------------------------------------------------------------
    report(4, "Taking cropped screenshot…")
    hide_ui()
    try:
        if capture_area == "mid":
            screenshot_bytes = _capture_cropped_screenshot(
                "cropicon.png", step=4, width=450, height=600,
                offset_x=450, offset_y=0
            )
        else:
            screenshot_bytes = _capture_cropped_screenshot(
                "cropicon.png", step=4, width=1135, height=635
            )
    finally:
        show_ui()

    # ------------------------------------------------------------------
    # Step 5  –  Find & click 'xinghuituce' button (Skip if requested)
    # ------------------------------------------------------------------
    if skip_album:
        report(5, "Skipping Xinghuituce (Save to Album) button…")
    else:
        report(5, "Looking for Xinghuituce button…")
        _find_and_click("xinghuituce.png", step=5, description="Xinghuituce (星绘图册)")

    # ------------------------------------------------------------------
    # Step 6  –  Pause 2 seconds
    # ------------------------------------------------------------------
    if skip_album:
        report(6, "Skipping wait for album save…")
    else:
        report(6, "Waiting…")
        time.sleep(2)

    # ------------------------------------------------------------------
    # Step 7  –  Find & click 'qianwangfenxiang' button
    # ------------------------------------------------------------------
    report(7, "Looking for Qianwangfenxiang button…")
    _find_and_click("qianwangfenxiang.png", step=7,
                    description="Qianwangfenxiang (前往分享)")

    # ------------------------------------------------------------------
    # Step 8  –  Pause 2 seconds
    # ------------------------------------------------------------------
    report(8, "Waiting for share page to load…")
    time.sleep(2)

    # ------------------------------------------------------------------
    # Step 9  –  Find & click 'copysharelink'
    #            Retry every 2 s for up to 120 s; fail if not found
    # ------------------------------------------------------------------
    report(9, "Waiting for Copy Share Link button (up to 2 minutes)…")
    _find_and_click(
        "copysharelink.png",
        step=9,
        description="Copy Share Link",
        timeout=120.0,
        retry_interval=2.0,
    )

    # ------------------------------------------------------------------
    # Step 10  –  Pause 2 seconds, then read clipboard
    # ------------------------------------------------------------------
    report(10, "Reading share link from clipboard…")
    time.sleep(2)
    share_text = _read_clipboard()

    return screenshot_bytes, share_text

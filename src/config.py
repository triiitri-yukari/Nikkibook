"""
Configuration module for NikkiBook.
Handles application paths and constants.
"""
import os
import sys
from pathlib import Path

# Application name for directory creation
APP_NAME = "NikkiBook"

# Get the directory where the application is located.
#
# Source runs keep the existing project-root behavior. Frozen builds use the
# directory beside the executable for portable data instead.
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    DATA_DIR = APP_DIR
else:
    APP_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = APP_DIR

# Runtime resources live inside the private PyInstaller folder in frozen
# builds, while source runs read them from the project assets folder.
if getattr(sys, "frozen", False):
    RUNTIME_RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR)) / "resources"
else:
    RUNTIME_RESOURCE_DIR = APP_DIR / "assets"

APP_ICON_PATH = RUNTIME_RESOURCE_DIR / "icon.ico"

# Use the portable data directory for packaged runs.
IMAGES_DIR = DATA_DIR / "images"
THUMBS_DIR = DATA_DIR / "thumbs"
ASSETS_CLICKER_DIR = APP_DIR / "assets clicker"

# Database path
DB_PATH = DATA_DIR / "nikkibook.db"

# Thumbnail settings
THUMBNAIL_SIZE = (200, 200)  # Width x Height in pixels

# Gallery settings
# Fallback/minimum column count used before the viewport width is known;
# the gallery otherwise derives columns responsively from its width.
GRID_COLUMNS = 4
THUMBNAIL_SPACING = 16  # Pixels between thumbnails

# Snap screenshot crop settings (width x height in pixels)
SNAP_CAPTURE_DEFAULT_SIZE = (450, 600)
SNAP_CAPTURE_DEFAULT_OFFSET_X = 450
SNAP_CAPTURE_MAX_DIMENSION = 32768

# Supported image formats (extensions without dot)
SUPPORTED_FORMATS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'tif'}

# Number of thumbnail cards created per event-loop tick, and the max batch
# of thumbnails queued for lazy loading at a time.
BATCH_SIZE = 20


def ensure_directories() -> None:
    """
    Create all required application directories if they don't exist.
    Called on application startup.
    """
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)


def get_image_path(filename: str) -> Path:
    """Get the full path to an image file in the images directory."""
    return IMAGES_DIR / filename


def get_thumbnail_path(image_id: str) -> Path:
    """Get the full path to a thumbnail file in the thumbs directory."""
    return THUMBS_DIR / f"{image_id}_thumb.jpg"


def is_supported_format(filepath: str | Path) -> bool:
    """Check if a file has a supported image format based on extension."""
    ext = Path(filepath).suffix.lower().lstrip('.')
    return ext in SUPPORTED_FORMATS

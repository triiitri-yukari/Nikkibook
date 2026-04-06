"""
Configuration module for NikkiBook.
Handles application paths and constants.
"""
import os
from pathlib import Path

# Application name for directory creation
APP_NAME = "NikkiBook"

# Get the directory where the application is located
# This will be the directory containing main.py
APP_DIR = Path(__file__).parent.parent.absolute()

# Use application directory for data storage
IMAGES_DIR = APP_DIR / "images"
THUMBS_DIR = APP_DIR / "thumbs"
ASSETS_CLICKER_DIR = APP_DIR / "assets clicker"

# Database path
DB_PATH = APP_DIR / "nikkibook.db"

# Thumbnail settings
THUMBNAIL_SIZE = (200, 200)  # Width x Height in pixels

# Gallery settings
GRID_COLUMNS = 4  # Number of columns in thumbnail grid
THUMBNAIL_SPACING = 16  # Pixels between thumbnails

# Supported image formats (extensions without dot)
SUPPORTED_FORMATS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'tif'}

# Maximum images to load per batch (for lazy loading)
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

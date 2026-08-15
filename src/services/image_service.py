"""
Image service for NikkiBook.
Handles importing, copying, and managing image files.
"""
import shutil
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from ..config import IMAGES_DIR, SUPPORTED_FORMATS, is_supported_format, get_image_path, get_thumbnail_path
from .. import database


def validate_share_string(share_string: str) -> Tuple[bool, str]:
    """
    Validate a share string. 
    Always returns valid as users can put any string.
    """
    return True, ""


def generate_short_id() -> str:
    """Generate a short 8-character hex ID."""
    return uuid.uuid4().hex[:8]


def generate_unique_filename(original_path: Path) -> str:
    """
    Generate a short-ID-based filename preserving the original extension.
    
    Args:
        original_path: Path to the original file
        
    Returns:
        New filename like 'a1b2c3d4.ext'
    """
    ext = original_path.suffix.lower()
    return f"{generate_short_id()}{ext}"


def import_image_from_path(
    source_path: str | Path,
    category_id: str,
    subcategory_id: Optional[str] = None,
    name: Optional[str] = None,
    share_string: str = ""
) -> Optional[str]:
    """
    Import an image from a file path into the catalog.
    
    Process:
    1. Validate the file exists and has a supported format
    2. Generate UUID filename
    3. Copy to images/ directory
    4. Create database record
    
    Args:
        source_path: Path to the source image file
        category_id: Category to assign the image to
        subcategory_id: Optional subcategory
        name: Optional display name
        share_string: Optional share URL
        
    Returns:
        The new image ID if successful, None if failed
    """
    source = Path(source_path)
    
    # Validate source exists
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")
    
    # Validate format
    if not is_supported_format(source):
        raise ValueError(f"Unsupported image format: {source.suffix}")
    
    # Validate share string if provided
    is_valid, error = validate_share_string(share_string)
    if not is_valid:
        raise ValueError(error)
    
    # Generate new filename and ID
    image_id = generate_short_id()
    new_filename = f"{image_id}{source.suffix.lower()}"
    dest_path = IMAGES_DIR / new_filename
    
    # Copy file
    try:
        shutil.copy2(source, dest_path)
    except Exception as e:
        raise IOError(f"Failed to copy image: {e}")
    
    # Create database record
    try:
        database.create_image(
            image_id=image_id,
            name=name,
            filename=new_filename,
            original_filename=source.name,
            category_id=category_id,
            subcategory_id=subcategory_id,
            share_string=share_string,
            created_at=datetime.now().isoformat()
        )
    except Exception as e:
        # Cleanup copied file on DB failure
        dest_path.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to create database record: {e}")
    
    return image_id


def import_image_from_bytes(
    data: bytes,
    extension: str,
    category_id: str,
    subcategory_id: Optional[str] = None,
    name: Optional[str] = None,
    share_string: str = ""
) -> Optional[str]:
    """
    Import an image from raw bytes (e.g., clipboard).
    
    Args:
        data: Raw image bytes
        extension: File extension (without dot, e.g., 'png')
        category_id: Category to assign the image to
        subcategory_id: Optional subcategory
        name: Optional display name
        share_string: Optional share URL
        
    Returns:
        The new image ID if successful, None if failed
    """
    # Validate extension
    ext = extension.lower().lstrip('.')
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported image format: {ext}")
    
    # Validate share string
    is_valid, error = validate_share_string(share_string)
    if not is_valid:
        raise ValueError(error)
    
    # Generate filename and save
    image_id = generate_short_id()
    new_filename = f"{image_id}.{ext}"
    dest_path = IMAGES_DIR / new_filename
    
    try:
        dest_path.write_bytes(data)
    except Exception as e:
        raise IOError(f"Failed to write image: {e}")
    
    # Create database record
    try:
        database.create_image(
            image_id=image_id,
            name=name or f"Pasted image",
            filename=new_filename,
            original_filename=None,
            category_id=category_id,
            subcategory_id=subcategory_id,
            share_string=share_string,
            created_at=datetime.now().isoformat()
        )
    except Exception as e:
        dest_path.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to create database record: {e}")
    
    return image_id


def delete_image(image_id: str) -> bool:
    """
    Delete an image from the catalog (file + database record + thumbnail).
    
    Args:
        image_id: ID of the image to delete
        
    Returns:
        True if deleted successfully
    """
    # Get filename before deleting from DB
    filename = database.delete_image(image_id)
    
    if filename:
        # Delete image file
        image_path = get_image_path(filename)
        image_path.unlink(missing_ok=True)
        
        # Delete thumbnail
        thumb_path = get_thumbnail_path(image_id)
        thumb_path.unlink(missing_ok=True)
        
        return True
    
    return False


def update_image_metadata(
    image_id: str,
    name: Optional[str] = None,
    category_id: Optional[str] = None,
    subcategory_id: Optional[str] = None,
    share_string: Optional[str] = None
) -> None:
    """
    Update an image's metadata.
    
    Args:
        image_id: ID of the image to update
        name: New name (or None to keep unchanged)
        category_id: New category (or None to keep unchanged)
        subcategory_id: New subcategory (or None to keep unchanged)  
        share_string: New share string (or None to keep unchanged)
    """
    # Validate share string if being updated
    if share_string is not None:
        is_valid, error = validate_share_string(share_string)
        if not is_valid:
            raise ValueError(error)
    
    database.update_image(
        image_id=image_id,
        name=name,
        category_id=category_id,
        subcategory_id=subcategory_id,
        share_string=share_string
    )

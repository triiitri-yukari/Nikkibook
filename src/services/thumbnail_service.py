"""
Thumbnail service for NikkiBook.
Handles generating and caching image thumbnails using Pillow.
Thread-safe for use with Qt worker threads.
"""
import threading
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

from ..config import THUMBNAIL_SIZE, get_image_path, get_thumbnail_path


# Thread lock for file operations
_thumbnail_lock = threading.Lock()


def get_thumbnail(image_id: str, filename: str) -> Optional[Path]:
    """
    Get or generate a thumbnail for an image.
    
    If a cached thumbnail exists, returns its path.
    Otherwise generates a new thumbnail and caches it.
    
    Args:
        image_id: The image's unique ID
        filename: The image's filename in images/ directory
        
    Returns:
        Path to the thumbnail, or None if generation failed
    """
    thumb_path = get_thumbnail_path(image_id)
    
    # Return cached thumbnail if it exists
    if thumb_path.exists():
        return thumb_path
    
    # Generate new thumbnail
    return generate_thumbnail(image_id, filename)


def generate_thumbnail(image_id: str, filename: str) -> Optional[Path]:
    """
    Generate a thumbnail for an image and cache it to disk.
    
    Uses LANCZOS resampling for high-quality downscaling.
    Saves as JPEG for efficient storage.
    
    Args:
        image_id: The image's unique ID
        filename: The image's filename in images/ directory
        
    Returns:
        Path to the generated thumbnail, or None if failed
    """
    image_path = get_image_path(filename)
    thumb_path = get_thumbnail_path(image_id)
    
    if not image_path.exists():
        return None
    
    # Use lock to prevent concurrent writes to same thumbnail
    with _thumbnail_lock:
        # Double-check in case another thread just created it
        if thumb_path.exists():
            return thumb_path
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for JPEG output)
                if img.mode in ('RGBA', 'P'):
                    # Create white background for transparency
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[3])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail (modifies in place, maintains aspect ratio)
                img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                
                # Save as JPEG with good quality
                img.save(thumb_path, 'JPEG', quality=85, optimize=True)
                
            return thumb_path
            
        except Exception as e:
            # Log error but don't crash - thumbnails are not critical
            print(f"Failed to generate thumbnail for {filename}: {e}")
            return None


def delete_thumbnail(image_id: str) -> bool:
    """
    Delete a cached thumbnail.
    
    Args:
        image_id: The image's unique ID
        
    Returns:
        True if deleted, False if not found
    """
    thumb_path = get_thumbnail_path(image_id)
    if thumb_path.exists():
        thumb_path.unlink()
        return True
    return False


def regenerate_thumbnail(image_id: str, filename: str) -> Optional[Path]:
    """
    Force regeneration of a thumbnail (deletes existing first).
    
    Args:
        image_id: The image's unique ID
        filename: The image's filename
        
    Returns:
        Path to the new thumbnail, or None if failed
    """
    delete_thumbnail(image_id)
    return generate_thumbnail(image_id, filename)


def get_dominant_color(image_id: str, filename: str) -> Optional[Tuple[int, int, int]]:
    """
    Get the dominant color of an image for color-based sorting.
    
    Uses thumbnail for efficiency. Calculates average color weighted
    towards the center of the image.
    
    Args:
        image_id: The image's unique ID
        filename: The image's filename
        
    Returns:
        RGB tuple of dominant color, or None if failed
    """
    # Ensure thumbnail exists
    thumb_path = get_thumbnail(image_id, filename)
    if not thumb_path:
        return None
    
    try:
        with Image.open(thumb_path) as img:
            # Resize to small size for fast color averaging
            small = img.resize((10, 10), Image.Resampling.LANCZOS)
            
            # Get all pixels
            pixels = list(small.getdata())
            
            if not pixels:
                return None
            
            # Calculate average color
            r = sum(p[0] for p in pixels) // len(pixels)
            g = sum(p[1] for p in pixels) // len(pixels)
            b = sum(p[2] for p in pixels) // len(pixels)
            
            return (r, g, b)
            
    except Exception as e:
        print(f"Failed to get dominant color for {filename}: {e}")
        return None


def rgb_to_hue(rgb: Tuple[int, int, int]) -> float:
    """
    Convert RGB to HSL hue value for color sorting.
    
    Returns hue in range 0-360 degrees.
    """
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    delta = max_c - min_c
    
    if delta == 0:
        return 0.0
    elif max_c == r:
        hue = ((g - b) / delta) % 6
    elif max_c == g:
        hue = (b - r) / delta + 2
    else:
        hue = (r - g) / delta + 4
    
    return hue * 60

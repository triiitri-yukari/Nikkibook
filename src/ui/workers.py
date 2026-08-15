"""
Worker threads for NikkiBook.
Handles background operations to keep the UI responsive.
Uses Qt signals for thread-safe communication.
"""
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap
from pathlib import Path
from typing import List, Tuple

class ThumbnailWorker(QThread):
    """
    Worker thread for generating thumbnails in the background.
    
    Processes a batch of images and emits signals as each thumbnail
    becomes ready. This prevents the UI from freezing when loading
    many images.
    
    Signals:
        thumbnail_ready: Emitted when a thumbnail is generated.
                        Args: (image_id, QPixmap)
        batch_complete: Emitted when all thumbnails in the batch are done.
        error: Emitted if an error occurs. Args: (image_id, error_message)
    """
    
    thumbnail_ready = pyqtSignal(str, QPixmap)  # image_id, pixmap
    batch_complete = pyqtSignal()
    error = pyqtSignal(str, str)  # image_id, error_message
    
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._images: List[Tuple[str, str]] = []  # List of (image_id, filename)
        self._should_stop = False
    
    def set_images(self, images: List[Tuple[str, str]]) -> None:
        """
        Set the batch of images to process.
        
        Args:
            images: List of (image_id, filename) tuples
        """
        self._images = images
        self._should_stop = False
    
    def stop(self) -> None:
        """Request the worker to stop processing."""
        self._should_stop = True
    
    def run(self) -> None:
        """
        Process all images in the batch.
        
        For each image:
        1. Generate or retrieve cached thumbnail
        2. Load as QPixmap
        3. Emit thumbnail_ready signal
        """
        # Pillow is comparatively expensive to import. Keep it off the startup
        # path and load it only once thumbnail work actually begins.
        from ..services import thumbnail_service

        for image_id, filename in self._images:
            if self._should_stop:
                break
            
            try:
                # Get or generate thumbnail
                thumb_path = thumbnail_service.get_thumbnail(image_id, filename)
                
                if thumb_path and thumb_path.exists():
                    # Load as QPixmap (this is the thread-safe part of Qt)
                    pixmap = QPixmap(str(thumb_path))
                    if not pixmap.isNull():
                        self.thumbnail_ready.emit(image_id, pixmap)
                    else:
                        self.error.emit(image_id, "Failed to load thumbnail as pixmap")
                else:
                    self.error.emit(image_id, "Failed to generate thumbnail")
                    
            except Exception as e:
                self.error.emit(image_id, str(e))
        
        self.batch_complete.emit()


class ColorSortWorker(QThread):
    """
    Worker thread for calculating dominant colors for sorting.
    
    Processes images and calculates their dominant color hue values.
    Results are used for color-based sorting in the gallery.
    
    Signals:
        color_ready: Emitted when a color is calculated.
                    Args: (image_id, hue_value)
        complete: Emitted when all colors are calculated.
    """
    
    color_ready = pyqtSignal(str, float)  # image_id, hue
    complete = pyqtSignal(dict)  # {image_id: hue}
    
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._images: List[Tuple[str, str]] = []
        self._should_stop = False
    
    def set_images(self, images: List[Tuple[str, str]]) -> None:
        """Set images to process: list of (image_id, filename)"""
        self._images = images
        self._should_stop = False
    
    def stop(self) -> None:
        """Request stop."""
        self._should_stop = True
    
    def run(self) -> None:
        """Calculate colors for all images."""
        from ..services import thumbnail_service

        results = {}
        
        for image_id, filename in self._images:
            if self._should_stop:
                break
            
            try:
                color = thumbnail_service.get_dominant_color(image_id, filename)
                if color:
                    hue = thumbnail_service.rgb_to_hue(color)
                    results[image_id] = hue
                    self.color_ready.emit(image_id, hue)
            except Exception:
                pass  # Skip images that fail color extraction
        
        self.complete.emit(results)

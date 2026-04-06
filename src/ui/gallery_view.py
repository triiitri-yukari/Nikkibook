"""
Gallery view for NikkiBook.
Displays a masonry-style grid of image thumbnails with hover effects.
Matches the reference design from ref image_catalog_dashboard.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout,
    QLabel, QSizePolicy, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from typing import Optional, List, Dict
from pathlib import Path

from .thumbnail_widget import ThumbnailWidget
from .workers import ThumbnailWorker, ColorSortWorker
import src.ui.styles as styles
from ..config import GRID_COLUMNS, BATCH_SIZE, THUMBNAIL_SPACING
from .. import database


class GalleryView(QWidget):
    """
    Modern scrollable gallery showing image thumbnails in a responsive grid.
    
    Features:
    - Masonry-style responsive grid layout
    - Lazy loading of thumbnails via worker thread
    - Drag & drop support
    - Hover effects with gradient overlays
    
    Signals:
        image_clicked: Emitted when an image is clicked. Args: (image_id,)
        image_double_clicked: Emitted for editing. Args: (image_id,)
        files_dropped: Emitted when files are dropped. Args: (file_paths,)
        paste_requested: Emitted when Ctrl+V is pressed.
    """
    
    image_clicked = pyqtSignal(str)
    image_double_clicked = pyqtSignal(str)
    files_dropped = pyqtSignal(list)  # List of file paths
    paste_requested = pyqtSignal()
    sharelink_changed = pyqtSignal(str, str)  # (image_id, new_value)
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        
        self._images: List[dict] = []
        self._thumbnail_widgets: Dict[str, ThumbnailWidget] = {}
        self._color_cache: Dict[str, float] = {}  # image_id -> hue
        self._current_category_name: str = "All Images"
        
        # Workers
        self._thumb_worker: Optional[ThumbnailWorker] = None
        self._color_worker: Optional[ColorSortWorker] = None
        
        self._setup_ui()
        
        # Enable drag & drop
        self.setAcceptDrops(True)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header section with category name and count
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet(f"background-color: {styles.COLORS['background_light']};")
        header_layout = QVBoxLayout(self.header_widget)
        header_layout.setContentsMargins(32, 24, 32, 16)
        header_layout.setSpacing(4)
        
        self.title_label = QLabel("All Images")
        self.title_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {styles.COLORS['text_dark']};
        """)
        header_layout.addWidget(self.title_label)
        
        self.count_label = QLabel("Showing 0 images")
        self.count_label.setStyleSheet(f"""
            font-size: 13px;
            color: {styles.COLORS['text_medium']};
        """)
        header_layout.addWidget(self.count_label)
        
        layout.addWidget(self.header_widget)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {styles.COLORS['background_light']};
            }}
            {styles.SCROLLBAR_STYLE}
        """)
        
        # Container widget for the grid
        self.container = QWidget()
        self.container.setStyleSheet(f"background: {styles.COLORS['background_light']};")
        
        # Use a flow-like grid layout
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(24)
        self.grid.setContentsMargins(32, 8, 32, 32)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area, 1)
        
        # Empty state widget
        self.empty_widget = QWidget()
        self.empty_widget.setStyleSheet(f"background: {styles.COLORS['background_light']};")
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_icon = QLabel("📷")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon.setStyleSheet("font-size: 64px;")
        empty_layout.addWidget(empty_icon)
        
        empty_title = QLabel("No images yet")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {styles.COLORS['text_dark']};
            margin-top: 16px;
        """)
        empty_layout.addWidget(empty_title)
        
        empty_desc = QLabel("Drag & drop images here or use the Add button")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_desc.setStyleSheet(f"""
            font-size: 14px;
            color: {styles.COLORS['text_medium']};
        """)
        empty_layout.addWidget(empty_desc)
        
        self.empty_widget.hide()
        layout.addWidget(self.empty_widget)
    
    def set_category_info(self, name: str, count: int):
        """Update the header with category name and count."""
        self._current_category_name = name
        self.title_label.setText(name)
        self.count_label.setText(f"Showing {count} images in this category")
    
    def set_images(self, images: List[dict]):
        """
        Set the images to display in the gallery.
        Clears existing thumbnails and loads new ones.
        """
        self._images = images
        
        # Update count in header
        count = len(images)
        if count == 0:
            self.count_label.setText("No images")
        elif count == 1:
            self.count_label.setText("Showing 1 image")
        else:
            self.count_label.setText(f"Showing {count} images")
        
        self._rebuild_grid()
    
    def _rebuild_grid(self):
        """Clear and rebuild the thumbnail grid."""
        # Stop any running workers
        if self._thumb_worker and self._thumb_worker.isRunning():
            self._thumb_worker.stop()
            self._thumb_worker.wait()
        
        # Clear existing widgets
        for widget in self._thumbnail_widgets.values():
            widget.deleteLater()
        self._thumbnail_widgets.clear()
        
        # Clear grid layout
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Show empty state if no images
        if not self._images:
            self.empty_widget.show()
            self.scroll_area.hide()
            self.header_widget.hide()
            return
        
        self.empty_widget.hide()
        self.scroll_area.show()
        self.header_widget.show()
        
        # Calculate number of columns based on container width
        # Using 4 columns by default for masonry-like layout
        columns = 4
        
        # Create thumbnail widgets
        for i, img_data in enumerate(self._images):
            row = i // columns
            col = i % columns
            
            thumb_widget = ThumbnailWidget(img_data)
            thumb_widget.clicked.connect(self._on_thumbnail_clicked)
            thumb_widget.double_clicked.connect(self._on_thumbnail_double_clicked)
            thumb_widget.sharelink_changed.connect(self._on_sharelink_changed)
            
            self.grid.addWidget(thumb_widget, row, col)
            self._thumbnail_widgets[img_data['id']] = thumb_widget
        
        # Start loading thumbnails
        self._load_thumbnails()
    
    def _load_thumbnails(self):
        """Start worker thread to load thumbnails."""
        if not self._images:
            return
        
        # Prepare batch of images for the worker
        image_batch = [(img['id'], img['filename']) for img in self._images]
        
        # Create and start worker
        self._thumb_worker = ThumbnailWorker(self)
        self._thumb_worker.set_images(image_batch)
        self._thumb_worker.thumbnail_ready.connect(self._on_thumbnail_ready)
        self._thumb_worker.start()
    
    def _on_thumbnail_ready(self, image_id: str, pixmap: QPixmap):
        """Handle loaded thumbnail from worker."""
        if image_id in self._thumbnail_widgets:
            self._thumbnail_widgets[image_id].set_thumbnail(pixmap)
    
    def _on_thumbnail_clicked(self, image_id: str):
        """Handle thumbnail click."""
        self.image_clicked.emit(image_id)
    
    def _on_thumbnail_double_clicked(self, image_id: str):
        """Handle thumbnail double-click."""
        self.image_double_clicked.emit(image_id)
    
    def _on_sharelink_changed(self, image_id: str, new_value: str):
        """Handle sharelink change from thumbnail widget."""
        self.sharelink_changed.emit(image_id, new_value)
    
    def refresh_image(self, image_id: str):
        """Refresh a single image's display after edit."""
        if image_id not in self._thumbnail_widgets:
            return
        
        # Get updated data from database
        image_data = database.get_image_by_id(image_id)
        if image_data:
            self._thumbnail_widgets[image_id].update_data(image_data)
    
    def remove_image(self, image_id: str):
        """Remove an image from the gallery."""
        if image_id in self._thumbnail_widgets:
            widget = self._thumbnail_widgets.pop(image_id)
            widget.deleteLater()
            
            # Rebuild grid to fix layout
            self._images = [img for img in self._images if img['id'] != image_id]
            self._rebuild_grid()
    
    # ========================================================================
    # Drag & Drop Support
    # ========================================================================
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter - accept if it contains file URLs."""
        if event.mimeData().hasUrls():
            # Check if any files are images
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path = Path(url.toLocalFile())
                    if path.suffix.lower().lstrip('.') in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'tif'}:
                        event.acceptProposedAction()
                        return
        event.ignore()
    
    def dragMoveEvent(self, event):
        """Accept drag move events."""
        event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle file drop."""
        file_paths = []
        
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                if path.suffix.lower().lstrip('.') in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'tif'}:
                    file_paths.append(str(path))
        
        if file_paths:
            event.acceptProposedAction()
            self.files_dropped.emit(file_paths)
    
    # ========================================================================
    # Keyboard Support
    # ========================================================================
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        # Ctrl+V for paste
        if event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.paste_requested.emit()
            return
        super().keyPressEvent(event)
    
    # ========================================================================
    # Color Sorting
    # ========================================================================
    
    def sort_by_color(self):
        """Sort images by their dominant color hue."""
        if not self._images:
            return
        
        # Check if we have cached colors
        if len(self._color_cache) >= len(self._images):
            self._apply_color_sort()
            return
        
        # Start color worker if needed
        if self._color_worker and self._color_worker.isRunning():
            return
        
        image_batch = [(img['id'], img['filename']) for img in self._images]
        self._color_worker = ColorSortWorker(self)
        self._color_worker.set_images(image_batch)
        self._color_worker.complete.connect(self._on_colors_ready)
        self._color_worker.start()
    
    def _on_colors_ready(self, colors: Dict[str, float]):
        """Handle completed color calculation."""
        self._color_cache.update(colors)
        self._apply_color_sort()
    
    def _apply_color_sort(self):
        """Apply the color-based sort to images."""
        def get_hue(img):
            return self._color_cache.get(img['id'], 0)
        
        self._images.sort(key=get_hue)
        self._rebuild_grid()
    
    def sort_by_date(self, newest_first: bool = True):
        """Sort images by creation date."""
        self._images.sort(
            key=lambda img: img.get('created_at', ''),
            reverse=newest_first
        )
        self._rebuild_grid()

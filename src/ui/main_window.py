"""
Main window for NikkiBook.
Modern UI with header bar, sidebar, and masonry-style gallery.
Matches the reference design from ref image_catalog_dashboard.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLineEdit, QComboBox, QPushButton, QLabel, QApplication,
    QMessageBox, QFrame, QSizePolicy
)
import tempfile
from PyQt6.QtCore import Qt, QMimeData, QByteArray, QSize, QSettings, QTimer
from PyQt6.QtGui import QClipboard, QImage, QKeySequence, QShortcut, QIcon, QFont, QFontDatabase
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import uuid
import tempfile

from .category_tree import CategoryTree
from .gallery_view import GalleryView
from .image_details_panel import ImageDetailsModal
from .dialogs import (
    AddImageDialog, EditImageDialog, AddCategoryDialog,
    show_error, show_warning, confirm_delete, SnapProgressDialog,
    SettingsDialog
)
from .snap_worker import SnapWorker
from .icons import icon as ui_icon, pixmap as ui_pixmap, icon_size
import src.ui.styles as styles
from .. import database
from ..services import image_service
from ..config import SUPPORTED_FORMATS
from .. import i18n as _i18n


def t(key: str, **kw) -> str:
    return _i18n.t(key, **kw)


class MainWindow(QMainWindow):
    """
    Main application window with modern UI.
    
    Layout:
    ┌──────────────────────────────────────────────────────────────────┐
    │ [Logo]  [Search________________________]  Sort: [Sort] [Add] [Settings] │
    ├──────────────┬───────────────────────────────────────────────────┤
    │   Sidebar    │                                                   │
    │  [+Cat][+Sub]│              Gallery                              │
    │  [Show All]  │           (Masonry Grid)                          │
    │   Category   │                                                   │
    │    └─ Sub    │                                                   │
    └──────────────┴───────────────────────────────────────────────────┘
    """
    
    def __init__(self):
        super().__init__()
        
        self._current_category_id: Optional[str] = None
        self._current_subcategory_id: Optional[str] = None
        self._current_search: str = ""
        self._current_sort: str = "newest"
        self._selected_image_id: Optional[str] = None
        self._initial_load_pending = True
        
        self._setup_ui()
        self._setup_shortcuts()
        
        # Subscribe to language changes for live UI updates
        _i18n.get_manager().language_changed.connect(self._retranslate)

    def showEvent(self, event):
        """Let the window paint before doing the initial gallery population."""
        super().showEvent(event)
        if self._initial_load_pending:
            self._initial_load_pending = False
            QTimer.singleShot(0, self._load_images)
    
    def _setup_ui(self):
        self.setWindowTitle("NikkiBook")
        self.setMinimumSize(1100, 750)
        self.resize(1400, 900)
        self.setStyleSheet(styles.MAIN_WINDOW_STYLE + styles.SCROLLBAR_STYLE)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ====================================================================
        # Header Bar
        # ====================================================================
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(80)
        header.setStyleSheet(f"""
            QWidget#header {{
                background-color: #DA9FBC;
                border-bottom: none;
            }}
            QWidget#header QWidget, QWidget#header QLabel {{
                background-color: transparent;
            }}
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        header_layout.setSpacing(24)
        
        # Logo
        logo_container = QHBoxLayout()
        logo_container.setContentsMargins(32, 0, 0, 0)  # push right toward center
        
        logo_text = QLabel("nikkibook")
        logo_text.setStyleSheet("""
            QLabel {
                font-family: 'Playwrite DK Uloopet Guides';
                font-size: 24px;
                font-weight: 550;
                color: white;
                background: transparent;
            }
        """)
        logo_container.addWidget(logo_text)
        
        header_layout.addLayout(logo_container)
        
        # Search bar with icon
        search_container = QWidget()
        search_container.setMaximumWidth(600)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t("search_placeholder"))
        self.search_input.setStyleSheet(styles.SEARCH_INPUT_STYLE)
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self._on_search_changed)
        
        # Use the bundled outline icon set so the search affordance is
        # identical in source and portable builds.
        self.search_icon_overlay = QLabel(self.search_input)
        self.search_icon_overlay.setPixmap(ui_pixmap("search", styles.COLORS['text_light'], 16))
        self.search_icon_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.search_icon_overlay.setStyleSheet(f"""
            color: {styles.COLORS['text_light']}; 
            background: transparent; 
        """)
        self.search_icon_overlay.setGeometry(16, 11, 20, 20)
        self.search_icon_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        search_layout.addWidget(self.search_input)
        
        header_layout.addWidget(search_container, 1)
        
        # Right side controls
        controls = QHBoxLayout()
        controls.setSpacing(16)
        
        # Sort dropdown
        sort_container = QHBoxLayout()
        sort_container.setSpacing(8)
        
        self._sort_label = QLabel(t("sort_label"))
        self._sort_label.setStyleSheet(f"color: {styles.COLORS['text_medium']}; font-size: 13px; font-weight: 500;")
        sort_container.addWidget(self._sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItem(t("sort_newest"), "newest")
        self.sort_combo.addItem(t("sort_oldest"), "oldest")
        self.sort_combo.addItem(t("sort_name"), "name")
        self.sort_combo.setStyleSheet(styles.SORT_COMBO_STYLE)
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        sort_container.addWidget(self.sort_combo)
        
        controls.addLayout(sort_container)
        
        # Add Image button
        self._add_btn = QPushButton(t("add_image_btn"))
        self._add_btn.setStyleSheet(styles.PRIMARY_BUTTON_STYLE)
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(self._add_image_dialog)
        controls.addWidget(self._add_btn)
        
        # Snap button
        self.snap_btn = QPushButton()
        self.snap_btn.setIcon(ui_icon("camera", "white"))
        self.snap_btn.setIconSize(icon_size(20))
        self.snap_btn.setFixedSize(48, 40)
        self.snap_btn.setToolTip(t("snap_title"))
        self.snap_btn.setStyleSheet(styles.PRIMARY_BUTTON_STYLE)
        self.snap_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.snap_btn.clicked.connect(self._on_snap_clicked)
        controls.addWidget(self.snap_btn)
        # Apply saved visibility immediately
        self._apply_snap_visibility()
        
        # Settings button
        settings_btn = QPushButton()
        settings_btn.setIcon(ui_icon("settings", styles.COLORS['text_dark']))
        settings_btn.setIconSize(icon_size(19))
        settings_btn.setFixedSize(44, 40)
        settings_btn.setToolTip(t("settings_title"))
        settings_btn.setStyleSheet(styles.ICON_BUTTON_STYLE)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self._show_settings)
        controls.addWidget(settings_btn)
        
        header_layout.addLayout(controls)
        main_layout.addWidget(header)
        
        # ====================================================================
        # Main Content Area: Sidebar + Gallery
        # ====================================================================
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Splitter for resizable sidebar
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {styles.COLORS['border']};
            }}
        """)
        
        # Left pane: Sidebar with category tree
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(f"""
            QWidget#sidebar {{
                background-color: {styles.COLORS['sidebar_light']};
            }}
        """)
        sidebar.setMinimumWidth(240)
        sidebar.setMaximumWidth(350)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 20)
        sidebar_layout.setSpacing(12)
        
        # Category tree component
        self.category_tree = CategoryTree()
        self.category_tree.selection_changed.connect(self._on_category_selected)
        self.category_tree.data_changed.connect(self._on_categories_changed)
        sidebar_layout.addWidget(self.category_tree)
        
        splitter.addWidget(sidebar)
        
        # Right pane: Gallery
        gallery_container = QWidget()
        gallery_container.setStyleSheet(f"background-color: {styles.COLORS['background_light']};")
        gallery_layout = QVBoxLayout(gallery_container)
        gallery_layout.setContentsMargins(0, 0, 0, 0)
        gallery_layout.setSpacing(0)
        
        self.gallery = GalleryView()
        self.gallery.image_clicked.connect(self._on_image_clicked)
        self.gallery.image_double_clicked.connect(self._on_image_double_clicked)
        self.gallery.files_dropped.connect(self._on_files_dropped)
        self.gallery.paste_requested.connect(self._on_paste)
        self.gallery.sharelink_changed.connect(self._on_sharelink_changed)
        gallery_layout.addWidget(self.gallery)
        
        splitter.addWidget(gallery_container)
        
        # Set initial sizes (sidebar: 280px, gallery: rest)
        splitter.setSizes([280, 1100])
        
        content_layout.addWidget(splitter)
        main_layout.addWidget(content_area, 1)
        
        # Modal overlay (not in splitter, overlays entire window)
        self.details_modal = ImageDetailsModal(central)
        self.details_modal.name_changed.connect(self._on_details_name_changed)
        self.details_modal.sharelink_changed.connect(self._on_details_sharelink_changed)
        self.details_modal.category_changed.connect(self._on_details_category_changed)
        self.details_modal.subcategory_changed.connect(self._on_details_subcategory_changed)
        self.details_modal.delete_requested.connect(self._on_details_delete_requested)
        self.details_modal.closed.connect(self._on_modal_closed)
        self.details_modal.hide()
    
    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Ctrl+V for paste (also handled in gallery)
        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
        paste_shortcut.activated.connect(self._on_paste)
        
        # Ctrl+F for search focus
        search_shortcut = QShortcut(QKeySequence.StandardKey.Find, self)
        search_shortcut.activated.connect(lambda: self.search_input.setFocus())
        
        # Escape to close modal
        escape_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        escape_shortcut.activated.connect(self._close_modal_if_open)
    
    def _close_modal_if_open(self):
        """Close the details modal if it's open."""
        if self.details_modal.isVisible():
            self.details_modal.hide()
            self.details_modal.clear()
            self._selected_image_id = None
    
    def _load_images(self):
        """Load images based on current filters."""
        if self._current_search:
            # Search mode
            images = database.search_images(self._current_search)
        elif self._current_category_id:
            # Category filter
            images = database.get_images_by_category(
                self._current_category_id,
                self._current_subcategory_id
            )
        else:
            # Show all
            images = database.get_all_images()
        
        # Apply sorting and update header
        self._apply_sort(images)
        
        # Update gallery header with category name and count
        self._update_gallery_header()
    
    def _update_gallery_header(self):
        """Update the gallery header with current category info."""
        # This could be expanded to show category name and image count
        # in the gallery area like the reference design
        pass
    
    def _apply_sort(self, images: List[dict]):
        """Apply current sort and update gallery."""
        sort_type = self.sort_combo.currentData()
        
        if sort_type == "newest":
            images.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            self.gallery.set_images(images)
        elif sort_type == "oldest":
            images.sort(key=lambda x: x.get('created_at', ''), reverse=False)
            self.gallery.set_images(images)
        elif sort_type == "name":
            images.sort(key=lambda x: (x.get('name') or x.get('original_filename') or '').lower())
            self.gallery.set_images(images)
        else:
            self.gallery.set_images(images)
    
    # ========================================================================
    # Event Handlers
    # ========================================================================
    
    def _on_search_changed(self, text: str):
        """Handle search input change."""
        self._current_search = text.strip()
        self._load_images()
    
    def _on_sort_changed(self, index: int):
        """Handle sort dropdown change."""
        self._load_images()
    
    def _on_category_selected(self, category_id: str, subcategory_id: Optional[str]):
        """Handle category tree selection."""
        self._current_category_id = category_id if category_id else None
        self._current_subcategory_id = subcategory_id
        self._current_search = ""  # Clear search when selecting category
        self.search_input.clear()
        self._load_images()
    
    def _on_categories_changed(self):
        """Handle category add/rename/delete."""
        # Reload images in case a category was deleted
        self._load_images()
    
    def _on_image_clicked(self, image_id: str):
        """Handle single click on image - show modal."""
        self._selected_image_id = image_id
        
        # Get image data
        image_data = database.get_image_by_id(image_id)
        if not image_data:
            return
        
        # Show modal
        categories = self.category_tree.get_categories()
        subcategories = self.category_tree.get_subcategories()
        self.details_modal.set_image(image_data, categories, subcategories)
    
    def _on_image_double_clicked(self, image_id: str):
        """Handle double-click to edit image."""
        self._edit_image(image_id)
    
    def _on_files_dropped(self, file_paths: List[str]):
        """Handle files dropped onto gallery."""
        self._import_files(file_paths)
    
    def _on_paste(self):
        """Handle paste from clipboard."""
        # Check if an input field has focus - if so, let the default paste handle it
        focused = QApplication.focusWidget()
        if isinstance(focused, (QLineEdit, QComboBox)):
            return

        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        # Check for image data
        if mime_data.hasImage():
            self._import_clipboard_image()
        # Check for file URLs
        elif mime_data.hasUrls():
            file_paths = []
            for url in mime_data.urls():
                if url.isLocalFile():
                    path = Path(url.toLocalFile())
                    if path.suffix.lower().lstrip('.') in SUPPORTED_FORMATS:
                        file_paths.append(str(path))
            if file_paths:
                self._import_files(file_paths)
    
    def _on_modal_closed(self):
        """Handle modal close."""
        self._selected_image_id = None
    
    def _on_details_name_changed(self, image_id: str, new_name: str):
        """Handle name change from details panel."""
        try:
            image_service.update_image_metadata(
                image_id=image_id,
                name=new_name
            )
            # Refresh the thumbnail to show updated name
            self.gallery.refresh_image(image_id)
        except Exception as e:
            show_error(self, t("update_error_title"), str(e))
    
    def _on_details_sharelink_changed(self, image_id: str, new_sharelink: str):
        """Handle sharelink change from details panel."""
        try:
            image_service.update_image_metadata(
                image_id=image_id,
                share_string=new_sharelink
            )
            # Refresh the thumbnail to show updated sharelink
            self.gallery.refresh_image(image_id)
        except Exception as e:
            show_error(self, t("update_error_title"), str(e))
            
    def _on_details_category_changed(self, image_id: str, new_category_id: str):
        """Handle category change from details panel."""
        try:
            image_service.update_image_metadata(
                image_id=image_id,
                category_id=new_category_id,
                subcategory_id=None  # Reset subcategory on category change
            )
            # Re-load images as it might have moved out of the current view
            self._load_images()
        except Exception as e:
            show_error(self, t("update_error_title"), str(e))
            
    def _on_details_subcategory_changed(self, image_id: str, new_subcategory_id: Optional[str]):
        """Handle subcategory change from details panel."""
        try:
            image_service.update_image_metadata(
                image_id=image_id,
                subcategory_id=new_subcategory_id
            )
            # Re-load images as it might have moved out of the current view
            self._load_images()
        except Exception as e:
            show_error(self, t("update_error_title"), str(e))
    
    def _on_details_delete_requested(self, image_id: str):
        """Handle delete request from modal."""
        # Get image data for confirmation
        image_data = database.get_image_by_id(image_id)
        if not image_data:
            return
        
        name = image_data.get('name') or image_data.get('original_filename') or 'Untitled'
        
        if confirm_delete(self, "Image", name):
            try:
                image_service.delete_image(image_id)
                self.gallery.remove_image(image_id)
                self.details_modal.hide()
                self.details_modal.clear()
                self._selected_image_id = None
            except Exception as e:
                show_error(self, t("delete_error_title"), str(e))
    
    def _on_sharelink_changed(self, image_id: str, new_value: str):
        """Handle inline sharelink edit from gallery."""
        try:
            image_service.update_image_metadata(
                image_id=image_id,
                share_string=new_value
            )
        except Exception as e:
            show_error(self, t("update_error_title"), str(e))
            # Reload the image to reset the value
            self.gallery.refresh_image(image_id)
    
    # ========================================================================
    # Image Operations
    # ========================================================================
    
    def _retranslate(self):
        """Re-apply all translatable strings and optimize font stack for current language."""
        lang = _i18n.get_manager().language
        
        # Update application-wide font stack based on current language
        app = QApplication.instance()
        if app:
            # 1. Update logical font database
            new_family = styles.get_font_family(lang)
            font = app.font()
            families = [f.strip(' "\'') for f in new_family.split(',')]
            font.setFamilies(families)
            app.setFont(font)
            
            # 2. Update global stylesheet to pick up new font-family fallback order
            app.setStyleSheet(styles.get_global_stylesheet(lang))
            
        self.search_input.setPlaceholderText(t("search_placeholder"))
        self._sort_label.setText(t("sort_label"))
        # Rebuild sort combo keeping current selection
        current_sort = self.sort_combo.currentData()
        self.sort_combo.blockSignals(True)
        self.sort_combo.clear()
        self.sort_combo.addItem(t("sort_newest"), "newest")
        self.sort_combo.addItem(t("sort_oldest"), "oldest")
        self.sort_combo.addItem(t("sort_name"), "name")
        idx = self.sort_combo.findData(current_sort)
        if idx >= 0:
            self.sort_combo.setCurrentIndex(idx)
        self.sort_combo.blockSignals(False)
        self._add_btn.setText(t("add_image_btn"))

    def _apply_snap_visibility(self):
        """Show or hide the snap button based on saved setting."""
        vis = QSettings("NikkiBook", "App").value("snap_button_visible", "show")
        self.snap_btn.setVisible(vis != "hide")

    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()
        # Refresh snap visibility in case user changed it
        self._apply_snap_visibility()

    def _add_image_dialog(self):
        """Show dialog to add a new image."""
        categories = self.category_tree.get_categories()
        subcategories = self.category_tree.get_subcategories()
        
        if not categories:
            show_warning(
                self,
                t("no_categories_title"),
                t("no_categories_msg")
            )
            return
        
        preselect_subcat = None if self._current_subcategory_id == "__none__" else self._current_subcategory_id
        dialog = AddImageDialog(
            categories,
            subcategories,
            self,
            preselect_category_id=self._current_category_id,
            preselect_subcategory_id=preselect_subcat
        )
        
        if dialog.exec():
            try:
                image_service.import_image_from_path(
                    source_path=dialog.get_file_path(),
                    category_id=dialog.get_category_id(),
                    subcategory_id=dialog.get_subcategory_id(),
                    name=dialog.get_name(),
                    share_string=dialog.get_share_string()
                )
                self._load_images()
            except Exception as e:
                show_error(self, "Import Error", str(e))
    
    def _import_files(self, file_paths: List[str]):
        """Import multiple files."""
        categories = self.category_tree.get_categories()
        
        if not categories:
            show_warning(
                self,
                "No Categories",
                "Please create a category first before adding images."
            )
            return
        
        # Use current category or first available
        category_id = self._current_category_id or categories[0][0]
        subcategory_id = None if self._current_subcategory_id == "__none__" else self._current_subcategory_id
        
        imported = 0
        errors = []
        
        for path in file_paths:
            try:
                image_service.import_image_from_path(
                    source_path=path,
                    category_id=category_id,
                    subcategory_id=subcategory_id
                )
                imported += 1
            except Exception as e:
                errors.append(f"{Path(path).name}: {e}")
        
        # Show results
        if errors:
            show_error(
                self,
                t("import_errors_title"),
                f"Imported {imported} image(s).\n\nErrors:\n" + "\n".join(errors[:5])
            )
        
        self._load_images()
    
    def _import_clipboard_image(self):
        """Import image from clipboard."""
        categories = self.category_tree.get_categories()
        
        if not categories:
            show_warning(
                self,
                t("no_categories_title"),
                t("no_categories_msg")
            )
            return
        
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        
        if image.isNull():
            show_warning(self, t("paste_error_title"), t("paste_no_image"))
            return
        
        # Save clipboard image to temp file, then import
        try:
            # Save as PNG temporarily
            temp_path = Path(tempfile.gettempdir()) / f"nikkibook_paste_{uuid.uuid4()}.png"
            image.save(str(temp_path), "PNG")
            
            category_id = self._current_category_id or categories[0][0]
            subcategory_id = None if self._current_subcategory_id == "__none__" else self._current_subcategory_id
            
            image_service.import_image_from_path(
                source_path=temp_path,
                category_id=category_id,
                subcategory_id=subcategory_id,
                name=""
            )
            
            # Clean up temp file
            temp_path.unlink(missing_ok=True)
            
            self._load_images()
            
        except Exception as e:
            show_error(self, t("paste_error_title"), str(e))
    
    def _edit_image(self, image_id: str):
        """Show dialog to edit an image."""
        image_data = database.get_image_by_id(image_id)
        if not image_data:
            show_error(self, t("error_title"), "Image not found.")
            return
        
        categories = self.category_tree.get_categories()
        subcategories = self.category_tree.get_subcategories()
        
        dialog = EditImageDialog(image_data, categories, subcategories, self)
        
        if dialog.exec():
            try:
                image_service.update_image_metadata(
                    image_id=image_id,
                    name=dialog.get_name(),
                    category_id=dialog.get_category_id(),
                    subcategory_id=dialog.get_subcategory_id(),
                    share_string=dialog.get_share_string()
                )
                self.gallery.refresh_image(image_id)
            except Exception as e:
                show_error(self, "Update Error", str(e))
    
    def _delete_image(self, image_id: str):
        """Delete an image after confirmation."""
        image_data = database.get_image_by_id(image_id)
        if not image_data:
            return
        
        name = image_data.get('name') or image_data.get('original_filename') or 'Untitled'
        
        if confirm_delete(self, "Image", name):
            try:
                image_service.delete_image(image_id)
                self.gallery.remove_image(image_id)
            except Exception as e:
                show_error(self, "Delete Error", str(e))
    
    # ========================================================================
    # Snap Automation
    # ========================================================================
    
    def _on_snap_clicked(self):
        """Start the snap automation workflow."""
        categories = self.category_tree.get_categories()

        if not categories:
            show_warning(
                self,
                t("no_categories_title"),
                t("no_categories_snap_msg")
            )
            return

        # Create progress dialog
        self._snap_progress = SnapProgressDialog(self)

        # Create and start worker
        self._snap_worker = SnapWorker()
        self._snap_worker.progress.connect(self._on_snap_progress)
        self._snap_worker.finished_snap.connect(self._on_snap_finished)
        self._snap_worker.error.connect(self._on_snap_error)
        self._snap_worker.hide_dialog.connect(self._on_snap_hide_dialog)
        self._snap_worker.show_dialog.connect(self._on_snap_show_dialog)

        # Cancel button re-enables the snap button and stops the worker
        self._snap_progress.rejected.connect(self._on_snap_cancelled)

        # Disable snap button while running
        self.snap_btn.setEnabled(False)

        self._snap_worker.start()
        self._snap_progress.show()

    def _on_snap_hide_dialog(self):
        """Hide the progress dialog so game window interaction is unobstructed."""
        if hasattr(self, '_snap_progress') and self._snap_progress:
            self._snap_progress.hide()

    def _on_snap_show_dialog(self):
        """Restore only the progress dialog — do NOT pull the main NikkiBook window to front."""
        if hasattr(self, '_snap_progress') and self._snap_progress:
            self._snap_progress.show()
            self._snap_progress.raise_()

    def _on_snap_cancelled(self):
        """Handle cancel button on the progress dialog."""
        # Terminate background worker
        if hasattr(self, '_snap_worker') and self._snap_worker and self._snap_worker.isRunning():
            self._snap_worker.terminate()
            self._snap_worker.wait(2000)
        # Re-enable snap button so user can try again
        self.snap_btn.setEnabled(True)
    
    def _on_snap_progress(self, step: int, description: str):
        """Update the snap progress dialog."""
        if hasattr(self, '_snap_progress') and self._snap_progress:
            self._snap_progress.update_progress(step, description)
    
    def _on_snap_finished(self, screenshot_bytes: bytes, share_text: str):
        """Handle successful snap completion."""
        # Close progress dialog
        if hasattr(self, '_snap_progress') and self._snap_progress:
            self._snap_progress.close()
        
        # Re-enable snap button
        self.snap_btn.setEnabled(True)
        
        # Bring NikkiBook window back to foreground
        self.activateWindow()
        self.raise_()
        
        # Import the screenshot
        categories = self.category_tree.get_categories()
        if not categories:
            show_error(self, t("snap_error_title"), t("snap_no_categories"))
            return
        
        category_id = self._current_category_id or categories[0][0]
        subcategory_id = None if self._current_subcategory_id == "__none__" else self._current_subcategory_id
        
        try:
            image_id = image_service.import_image_from_bytes(
                data=screenshot_bytes,
                extension='png',
                category_id=category_id,
                subcategory_id=subcategory_id,
                name="",
                share_string=share_text
            )
            
            self._load_images()
            
            # If we have an image_id and shares text, show the new image details
            if image_id:
                image_data = database.get_image_by_id(image_id)
                if image_data:
                    categories_list = self.category_tree.get_categories()
                    subcategories_list = self.category_tree.get_subcategories()
                    self.details_modal.set_image(image_data, categories_list, subcategories_list)
            
        except Exception as e:
            show_error(self, t("snap_import_error"), f"Failed to save screenshot: {e}")
    
    def _on_snap_error(self, error_message: str):
        """Handle snap workflow error."""
        # Close progress dialog
        if hasattr(self, '_snap_progress') and self._snap_progress:
            self._snap_progress.close()
        
        # Re-enable snap button
        self.snap_btn.setEnabled(True)
        
        # Bring NikkiBook window back to foreground
        self.activateWindow()
        self.raise_()
        
        # Show error popup
        show_error(self, t("snap_error_title"), error_message)

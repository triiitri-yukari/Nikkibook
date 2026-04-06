"""
Image details modal dialog.
Modern two-column layout matching the reference design from ref edit_image_details.
Shows image preview on left, form fields on right.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QApplication, QComboBox, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import pyqtSignal, Qt, QEvent, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QIcon
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime

from ..config import get_image_path
import src.ui.styles as styles
from .. import i18n as _i18n


def t(key: str, **kw) -> str:
    return _i18n.t(key, **kw)


class ImageDetailsModal(QWidget):
    """
    Modern modal dialog showing details of a selected image.
    
    Layout:
    ┌───────────────────────────────────────────────────┐
    │ [X]                                               │
    │  ┌─────────────────┬─────────────────────────┐   │
    │  │                 │  Edit Details           │   │
    │  │    Image        │  Category   Subcategory │   │
    │  │    Preview      │  [_______]  [_________] │   │
    │  │                 │                         │   │
    │  │   ┌─────────┐   │  Display Name           │   │
    │  │   │  INFO   │   │  [_____________________]│   │
    │  │   │ ID: xxx │   │                         │   │
    │  │   │ Added:  │   │  Share Link             │   │
    │  │   └─────────┘   │  [_____________________]│   │
    │  │                 │                         │   │
    │  │                 │  [Save Changes]         │   │
    │  │                 │  [Delete Image]         │   │
    │  └─────────────────┴─────────────────────────┘   │
    └───────────────────────────────────────────────────┘
    
    Signals:
        name_changed: Emitted when name is edited. Args: (image_id, new_name)
        sharelink_changed: Emitted when sharelink is edited. Args: (image_id, new_sharelink)
        delete_requested: Emitted when delete button is clicked. Args: (image_id,)
        closed: Emitted when modal is closed.
    """
    
    name_changed = pyqtSignal(str, str)  # (image_id, new_name)
    sharelink_changed = pyqtSignal(str, str)  # (image_id, new_sharelink)
    category_changed = pyqtSignal(str, str)  # (image_id, new_category_id)
    subcategory_changed = pyqtSignal(str, object)  # (image_id, new_subcategory_id)
    delete_requested = pyqtSignal(str)  # (image_id,)
    closed = pyqtSignal()
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        
        self._image_data: Optional[Dict] = None
        self._image_id: Optional[str] = None
        self._all_categories: List[Tuple[str, str]] = []
        self._all_subcategories: List[Tuple[str, str, str]] = []
        self._is_loading = False
        
        # Make this widget fill the parent and be transparent for overlay effect
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
        self.hide()
        
        # Live language updates
        _i18n.get_manager().language_changed.connect(self._retranslate)
    
    def _setup_ui(self):
        """Set up the modal UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Center the modal content
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        
        # Modal content frame (two-column layout)
        self.content_frame = QFrame()
        self.content_frame.setFixedSize(850, 550)
        self.content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {styles.COLORS['background_light']};
                border-radius: 24px;
            }}
        """)
        
        # Add shadow to modal
        shadow = QGraphicsDropShadowEffect(self.content_frame)
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.content_frame.setGraphicsEffect(shadow)
        
        content_layout = QHBoxLayout(self.content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # ====================================================================
        # Left side: Image preview with dark background
        # ====================================================================
        left_panel = QWidget()
        left_panel.setFixedWidth(350)
        left_panel.setStyleSheet(f"""
            QWidget {{
                background-color: #1e293b;
                border-top-left-radius: 24px;
                border-bottom-left-radius: 24px;
            }}
        """)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(24, 24, 24, 24)
        left_layout.setSpacing(16)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(40, 40)
        close_btn.setStyleSheet(styles.MODAL_CLOSE_BUTTON_STYLE)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self._close_modal)
        left_layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignLeft)
        
        left_layout.addStretch()
        
        # Image preview
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(300, 300)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: #334155;
                border-radius: 12px;
            }}
        """)
        self.preview_label.setScaledContents(False)
        left_layout.addWidget(self.preview_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        left_layout.addStretch()
        
        # Info box
        info_box = QFrame()
        info_box.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 12px;
                border: none;
                padding: 12px;
            }}
        """)
        
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(16, 12, 16, 12)
        info_layout.setSpacing(8)
        
        self._info_title_lbl = QLabel()
        self._info_title_lbl.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 700;
            color: {styles.COLORS['primary']};
            letter-spacing: 1px;
        """)
        info_layout.addWidget(self._info_title_lbl)
        
        info_content = QHBoxLayout()
        info_content.setSpacing(16)
        
        self.id_label = QLabel("ID: —")
        self.id_label.setStyleSheet(f"""
            font-size: 11px;
            color: rgba(255, 255, 255, 0.7);
        """)
        self.id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info_content.addWidget(self.id_label)
        
        self.date_label = QLabel("Added: —")
        self.date_label.setStyleSheet(f"""
            font-size: 11px;
            color: rgba(255, 255, 255, 0.7);
        """)
        info_content.addWidget(self.date_label)
        
        info_content.addStretch()
        info_layout.addLayout(info_content)
        
        left_layout.addWidget(info_box)
        
        content_layout.addWidget(left_panel)
        
        # ====================================================================
        # Right side: Form fields
        # ====================================================================
        right_panel = QWidget()
        right_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {styles.COLORS['sidebar_light']};
                border-top-right-radius: 24px;
                border-bottom-right-radius: 24px;
            }}
        """)
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(32, 32, 32, 32)
        right_layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        
        self._edit_title_lbl = QLabel()
        self._edit_title_lbl.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {styles.COLORS['text_dark']};
            background-color: transparent;
            border: none;
            padding: 0;
        """)
        header.addWidget(self._edit_title_lbl)
        
        header.addStretch()
        right_layout.addLayout(header)
        
        # Category and Subcategory row
        cat_row = QHBoxLayout()
        cat_row.setSpacing(16)
        
        # Category
        cat_container = QVBoxLayout()
        cat_container.setSpacing(6)
        
        self._cat_lbl = QLabel()
        self._cat_lbl.setStyleSheet(styles.FORM_LABEL_STYLE)
        cat_container.addWidget(self._cat_lbl)
        
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(190, 90, 141, 0.15);
                border: 1px solid rgba(190, 90, 141, 0.3);
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: {styles.COLORS['text_dark']};
                min-width: 150px;
            }}
            QComboBox:focus {{
                border: 2px solid {styles.COLORS['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {styles.COLORS['card_light']};
                border: 1px solid {styles.COLORS['border']};
                border-radius: 8px;
                selection-background-color: {styles.COLORS['primary']};
                selection-color: white;
            }}
        """)
        self.category_combo.currentIndexChanged.connect(self._on_category_combo_changed)
        cat_container.addWidget(self.category_combo)
        
        cat_row.addLayout(cat_container)
        
        # Subcategory
        subcat_container = QVBoxLayout()
        subcat_container.setSpacing(6)
        
        self._subcat_lbl = QLabel()
        self._subcat_lbl.setStyleSheet(styles.FORM_LABEL_STYLE)
        subcat_container.addWidget(self._subcat_lbl)
        
        self.subcategory_combo = QComboBox()
        self.subcategory_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(190, 90, 141, 0.15);
                border: 1px solid rgba(190, 90, 141, 0.3);
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: {styles.COLORS['text_dark']};
                min-width: 150px;
            }}
            QComboBox:focus {{
                border: 2px solid {styles.COLORS['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {styles.COLORS['card_light']};
                border: 1px solid {styles.COLORS['border']};
                border-radius: 8px;
                selection-background-color: {styles.COLORS['primary']};
                selection-color: white;
            }}
        """)
        self.subcategory_combo.currentIndexChanged.connect(self._on_subcategory_combo_changed)
        subcat_container.addWidget(self.subcategory_combo)
        
        cat_row.addLayout(subcat_container)
        cat_row.addStretch()
        
        right_layout.addLayout(cat_row)
        
        # Display name field
        name_container = QVBoxLayout()
        name_container.setSpacing(6)
        
        self._name_lbl = QLabel()
        self._name_lbl.setStyleSheet(styles.FORM_LABEL_STYLE)
        name_container.addWidget(self._name_lbl)
        
        self.name_field = QLineEdit()
        self.name_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(190, 90, 141, 0.15);
                border: 1px solid rgba(190, 90, 141, 0.3);
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 13px;
                color: {styles.COLORS['text_dark']};
            }}
            QLineEdit:focus {{
                border: 2px solid {styles.COLORS['primary']};
                background-color: {styles.COLORS['card_light']};
            }}
        """)
        self.name_field.editingFinished.connect(self._on_name_edited)
        name_container.addWidget(self.name_field)
        
        right_layout.addLayout(name_container)
        
        # Sharecode field
        share_container = QVBoxLayout()
        share_container.setSpacing(6)
        
        self._share_lbl = QLabel()
        self._share_lbl.setStyleSheet(styles.FORM_LABEL_STYLE)
        share_container.addWidget(self._share_lbl)
        
        share_row = QHBoxLayout()
        share_row.setSpacing(0)
        
        self.sharelink_field = QLineEdit()
        self.sharelink_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(190, 90, 141, 0.15);
                border: 1px solid rgba(190, 90, 141, 0.3);
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
                border-top-right-radius: 0;
                border-bottom-right-radius: 0;
                padding: 12px 16px;
                font-size: 13px;
                color: {styles.COLORS['text_dark']};
            }}
            QLineEdit:focus {{
                border: 2px solid {styles.COLORS['primary']};
                background-color: {styles.COLORS['card_light']};
            }}
        """)
        self.sharelink_field.editingFinished.connect(self._on_sharelink_edited)
        share_row.addWidget(self.sharelink_field, 1)
        
        # Copy button (replacing status indicator)
        self.share_copy_btn = QPushButton()
        self.share_copy_btn.setFixedSize(44, 44)
        self.share_copy_btn.setToolTip("Copy to clipboard")
        self.share_copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Create copy and tick icons for the button
        def create_copy_icon_details(color):
            from PyQt6.QtGui import QPixmap, QPainter
            from PyQt6.QtCore import QRectF
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = painter.pen()
            pen.setColor(QColor(color))
            pen.setWidth(1)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            back_rect = QRectF(7, 7, 10, 10)
            painter.drawRoundedRect(back_rect, 2, 2)
            front_rect = QRectF(3, 3, 10, 10)
            painter.drawRoundedRect(front_rect, 2, 2)
            painter.end()
            return QIcon(pixmap)
        
        def create_tick_icon_details(color):
            from PyQt6.QtGui import QPixmap, QPainter
            from PyQt6.QtCore import QPoint
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = painter.pen()
            pen.setColor(QColor(color))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(QPoint(6, 10), QPoint(9, 13))
            painter.drawLine(QPoint(9, 13), QPoint(14, 6))
            painter.end()
            return QIcon(pixmap)
        
        self.share_copy_icon = create_copy_icon_details(styles.COLORS['primary'])
        self.share_copy_icon_hover = create_copy_icon_details('white')
        self.share_tick_icon = create_tick_icon_details('white')
        
        self.share_copy_btn.setIcon(self.share_copy_icon)
        self.share_copy_btn.setIconSize(QSize(20, 20))
        
        # Install event filter to handle hover
        self.share_copy_btn.installEventFilter(self)
        
        self.share_copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(190, 90, 141, 0.15);
                border: 1px solid rgba(190, 90, 141, 0.3);
                border-left: none;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {styles.COLORS['primary']};
            }}
        """)
        self.share_copy_btn.clicked.connect(self._copy_sharecode)
        share_row.addWidget(self.share_copy_btn)
        
        share_container.addLayout(share_row)
        right_layout.addLayout(share_container)
        
        right_layout.addStretch()
        
        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {styles.COLORS['border']};")
        right_layout.addWidget(divider)
        
        # Delete button
        self.delete_btn = QPushButton()
        self.delete_btn.setStyleSheet(styles.DELETE_BUTTON_STYLE)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        right_layout.addWidget(self.delete_btn)
        
        content_layout.addWidget(right_panel, 1)
        
        center_layout.addWidget(self.content_frame)
        center_layout.addStretch()
        
        main_layout.addStretch()
        main_layout.addLayout(center_layout)
        main_layout.addStretch()
        
        # Apply initial language strings
        self._retranslate()
    
    def showEvent(self, event):
        """Override show event to resize to parent."""
        super().showEvent(event)
        if self.parent():
            self.resize(self.parent().size())
    
    def _retranslate(self):
        """Update all translatable UI strings."""
        self._info_title_lbl.setText(t("info_title"))
        self._edit_title_lbl.setText(t("edit_details_title"))
        self._cat_lbl.setText(t("category_label"))
        self._subcat_lbl.setText(t("subcategory_label"))
        self._name_lbl.setText(t("display_name_label_required"))
        self.name_field.setPlaceholderText(t("display_name_placeholder"))
        self._share_lbl.setText(t("sharecode_label_required"))
        self.sharelink_field.setPlaceholderText(t("sharecode_placeholder"))
        self.share_copy_btn.setToolTip(t("copy_tooltip"))
        self.delete_btn.setText(t("delete_image_btn"))
        # Update (None) option in subcategory combo
        for i in range(self.subcategory_combo.count()):
            if self.subcategory_combo.itemData(i) is None:
                self.subcategory_combo.setItemText(i, t("none_option"))
        # Update date / id labels if no image loaded
        if not self._image_data:
            self.id_label.setText(t("id_label"))
            self.date_label.setText(t("added_label"))
    
    def paintEvent(self, event):
        """Paint semi-transparent overlay background."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
    
    def mousePressEvent(self, event):
        """Close modal when clicking outside the content frame."""
        if not self.content_frame.geometry().contains(event.pos()):
            self._close_modal()
    
    def eventFilter(self, obj, event):
        """Handle events for child widgets, specifically copy button hover."""
        if obj == self.share_copy_btn:
            if event.type() == QEvent.Type.Enter:
                # Mouse entered button - change to white icon
                self.share_copy_btn.setIcon(self.share_copy_icon_hover)
            elif event.type() == QEvent.Type.Leave:
                # Mouse left button - change back to normal icon
                self.share_copy_btn.setIcon(self.share_copy_icon)
        return super().eventFilter(obj, event)
    
    def set_image(self, image_data: Dict, categories: List[Tuple[str, str]], subcategories: List[Tuple[str, str, str]]):
        """Load and display image details."""
        self._is_loading = True
        self._image_data = image_data
        self._image_id = image_data['id']
        self._all_categories = categories
        self._all_subcategories = subcategories
        
        # Load image preview
        image_path = get_image_path(image_data['filename'])
        if image_path.exists():
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    280, 280,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled)
        
        # Set info labels
        self.id_label.setText(f"ID: {image_data['id']}")
        
        # Format date
        created_at = image_data.get('created_at', '')
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%Y-%m-%d")
                self.date_label.setText(f"{t('added_prefix')} {formatted_date}")
            except:
                self.date_label.setText(t("added_label"))
        else:
            self.date_label.setText(t("added_label"))
        
        # Set field values
        self.name_field.setText(image_data.get('name') or '')
        self.sharelink_field.setText(image_data.get('share_string') or '')
        
        # Update copy button icon based on whether sharecode exists
        if image_data.get('share_string'):
            self.share_copy_btn.setIcon(self.share_copy_icon)
            self.share_copy_btn.setEnabled(True)
        else:
            self.share_copy_btn.setEnabled(False)
        
        # Populate Category combo
        self.category_combo.clear()
        current_cat_idx = -1
        for i, (cat_id, cat_name) in enumerate(self._all_categories):
            self.category_combo.addItem(cat_name, cat_id)
            if cat_id == image_data.get('category_id'):
                current_cat_idx = i
        
        if current_cat_idx >= 0:
            self.category_combo.setCurrentIndex(current_cat_idx)
        
        # Subcategory is populated by the index change handler
        self._update_subcategory_combo(image_data.get('category_id'), image_data.get('subcategory_id'))
        
        self._is_loading = False
        
        # Show modal
        self.show()
        self.raise_()
    
    def _update_subcategory_combo(self, category_id: str, selected_sub_id: Optional[str] = None):
        """Update subcategory dropdown based on selected category."""
        was_loading = self._is_loading
        self._is_loading = True
        
        self.subcategory_combo.clear()
        self.subcategory_combo.addItem("(None)", None)
        
        current_sub_idx = 0
        idx = 1
        for sub_id, sub_name, cat_id in self._all_subcategories:
            if cat_id == category_id:
                self.subcategory_combo.addItem(sub_name, sub_id)
                if sub_id == selected_sub_id:
                    current_sub_idx = idx
                idx += 1
        
        self.subcategory_combo.setCurrentIndex(current_sub_idx)
        self._is_loading = was_loading
    
    def clear(self):
        """Clear all fields."""
        self._image_data = None
        self._image_id = None
        self._all_categories = []
        self._all_subcategories = []
        self.preview_label.clear()
        self.id_label.setText(t("id_label"))
        self.date_label.setText(t("added_label"))
        self.name_field.clear()
        self.category_combo.clear()
        self.subcategory_combo.clear()
        self.sharelink_field.clear()
    
    def _close_modal(self):
        """Close the modal and emit closed signal."""
        self.hide()
        self.clear()
        self.closed.emit()
    
    def _on_name_edited(self):
        """Handle name field edit."""
        if not self._image_id or self._is_loading:
            return
        
        new_name = self.name_field.text().strip()
        old_name = self._image_data.get('name', '') if self._image_data else ''
        
        if new_name != old_name:
            self.name_changed.emit(self._image_id, new_name)
            if self._image_data:
                self._image_data['name'] = new_name
    
    def _on_sharelink_edited(self):
        """Handle sharelink field edit."""
        if not self._image_id or self._is_loading:
            return
        
        new_sharelink = self.sharelink_field.text().strip()
        old_sharelink = self._image_data.get('share_string', '') if self._image_data else ''
        
        if new_sharelink != old_sharelink:
            self.sharelink_changed.emit(self._image_id, new_sharelink)
            if self._image_data:
                self._image_data['share_string'] = new_sharelink
            
            # Update copy button state
            if new_sharelink:
                self.share_copy_btn.setIcon(self.share_copy_icon)
                self.share_copy_btn.setEnabled(True)
            else:
                self.share_copy_btn.setEnabled(False)
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        if self._image_id:
            self.delete_requested.emit(self._image_id)
            
    def _on_category_combo_changed(self, index: int):
        """Handle category combo change."""
        if self._is_loading or not self._image_id:
            return
            
        category_id = self.category_combo.currentData()
        if not category_id:
            return
            
        # Update subcategory combo for the new category
        self._update_subcategory_combo(category_id)
        
        # Emit signal
        self.category_changed.emit(self._image_id, category_id)
        if self._image_data:
            self._image_data['category_id'] = category_id
            self._image_data['subcategory_id'] = None  # Reset subcategory on category change
            
    def _on_subcategory_combo_changed(self, index: int):
        """Handle subcategory combo change."""
        if self._is_loading or not self._image_id:
            return
            
        subcategory_id = self.subcategory_combo.currentData()
        
        # Emit signal
        self.subcategory_changed.emit(self._image_id, subcategory_id)
        if self._image_data:
            self._image_data['subcategory_id'] = subcategory_id
    
    def _copy_sharecode(self):
        """Copy sharecode to clipboard with visual feedback."""
        share_text = self.sharelink_field.text().strip()
        if share_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(share_text)
            
            # Visual feedback - change to tick icon and success color
            self.share_copy_btn.setIcon(self.share_tick_icon)
            self.share_copy_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {styles.COLORS['success']};
                    border: 1px solid {styles.COLORS['success']};
                    border-left: none;
                    border-top-right-radius: 8px;
                    border-bottom-right-radius: 8px;
                }}
            """)
            
            # Reset after 0.2 seconds
            from PyQt6.QtCore import QTimer
            def reset_style():
                self.share_copy_btn.setIcon(self.share_copy_icon)
                self.share_copy_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(190, 90, 141, 0.15);
                        border: 1px solid rgba(190, 90, 141, 0.3);
                        border-left: none;
                        border-top-right-radius: 8px;
                        border-bottom-right-radius: 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {styles.COLORS['primary']};
                    }}
                """)
            QTimer.singleShot(200, reset_style)

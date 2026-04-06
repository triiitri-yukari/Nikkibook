"""
Thumbnail widget for NikkiBook.
Modern card component with hover effects matching the reference design.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QApplication, QLineEdit, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPropertyAnimation, QEasingCurve, QByteArray, QEvent
from PyQt6.QtGui import QPixmap, QMouseEvent, QColor, QPainter, QPainterPath, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from typing import Optional

import src.ui.styles as styles


class ThumbnailWidget(QFrame):
    """
    Modern card widget displaying a single image thumbnail.
    
    Features:
    - White card with rounded corners and shadow
    - Hover effect with gradient overlay
    - Sharecode input with copy button
    - Smooth animations
    
    Signals:
        clicked: Emitted when the thumbnail is clicked.
                Args: (image_id,)
        double_clicked: Emitted on double-click for editing.
                       Args: (image_id,)
    """
    
    clicked = pyqtSignal(str)
    double_clicked = pyqtSignal(str)
    sharelink_changed = pyqtSignal(str, str)  # (image_id, new_value)
    
    CARD_WIDTH = 240
    CARD_MIN_HEIGHT = 240
    THUMB_SIZE = 200
    
    def __init__(self, image_data: dict, parent: QWidget = None):
        super().__init__(parent)
        self._image_id = image_data['id']
        self._image_data = image_data
        self._pixmap: Optional[QPixmap] = None
        self._is_hovered = False
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedWidth(self.CARD_WIDTH)
        self.setFixedHeight(self.CARD_MIN_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Card styling with shadow effect
        self.setStyleSheet(f"""
            ThumbnailWidget {{
                background-color: {styles.COLORS['card_light']};
                border-radius: 16px;
                border: none;
            }}
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 25))
        self.setGraphicsEffect(shadow)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Image container (for gradient overlay on hover)
        self.image_container = QWidget()
        self.image_container.setFixedHeight(self.THUMB_SIZE)
        self.image_container.setStyleSheet(f"""
            background-color: #f1f5f9;
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
        """)
        
        image_layout = QVBoxLayout(self.image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(0)
        image_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Thumbnail label
        self.thumb_label = QLabel()
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("background: transparent;")
        self._set_placeholder()
        image_layout.addWidget(self.thumb_label)
        
        layout.addWidget(self.image_container)

        # Bottom section with sharecode
        bottom_section = QWidget()
        bottom_section.setStyleSheet(f"""
            background-color: {styles.COLORS['card_light']};
            border-bottom-left-radius: 16px;
            border-bottom-right-radius: 16px;
        """)
        
        bottom_layout = QVBoxLayout(bottom_section)
        bottom_layout.setContentsMargins(12, 8, 12, 8)
        bottom_layout.setSpacing(0)
        
        # Share code row
        share_row = QHBoxLayout()
        share_row.setSpacing(6)
        
        share_text = self._image_data.get('share_string', '')
        
        # Editable sharecode input
        self.share_edit = QLineEdit()
        self.share_edit.setText(share_text)
        self.share_edit.setPlaceholderText("Enter sharecode...")
        self.share_edit.setMaximumHeight(20)
        self.share_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                padding: 0;
                font-size: 10px;
                font-weight: 500;
                color: {styles.COLORS['text_medium']};
            }}
            QLineEdit:focus {{
                border: none;
                outline: none;
            }}
        """)
        self.share_edit.editingFinished.connect(self._on_sharecode_edited)
        share_row.addWidget(self.share_edit, 1)
        
        # Copy button with simple custom icon
        self.copy_btn = QPushButton()
        self.copy_btn.setFixedSize(20, 20)
        self.copy_btn.setToolTip("Copy to clipboard")
        
        # Create modern copy icon (two overlapping rounded rectangles)
        def create_copy_icon(color):
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Set color and pen
            pen = painter.pen()
            pen.setColor(QColor(color))
            pen.setWidth(1)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)  # No fill
            
            # Draw back rounded rectangle (offset down-right)
            from PyQt6.QtCore import QRectF
            back_rect = QRectF(5.5, 5.5, 8, 8)
            painter.drawRoundedRect(back_rect, 1.5, 1.5)
            
            # Draw front rounded rectangle (no fill)
            front_rect = QRectF(2.5, 2.5, 8, 8)
            painter.drawRoundedRect(front_rect, 1.5, 1.5)
            
            painter.end()
            return QIcon(pixmap)
        
        # Create tick icon for success feedback
        def create_tick_icon(color):
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Set color
            pen = painter.pen()
            pen.setColor(QColor(color))
            pen.setWidth(2)
            painter.setPen(pen)
            
            # Draw checkmark
            from PyQt6.QtCore import QPoint
            painter.drawLine(QPoint(4, 8), QPoint(7, 11))
            painter.drawLine(QPoint(7, 11), QPoint(12, 4))
            
            painter.end()
            return QIcon(pixmap)
        
        self.copy_icon_normal = create_copy_icon(styles.COLORS['primary'])
        self.copy_icon_hover = create_copy_icon('white')
        self.tick_icon = create_tick_icon('white')
        
        self.copy_btn.setIcon(self.copy_icon_normal)
        self.copy_btn.setIconSize(QSize(16, 16))
        
        # Install event filter to handle hover
        self.copy_btn.installEventFilter(self)
        
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f1f5f9;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {styles.COLORS['primary']};
            }}
            QPushButton:disabled {{
                background-color: #e2e8f0;
                opacity: 0.5;
            }}
        """)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy_share_string)
        self.copy_btn.setEnabled(bool(share_text))
        share_row.addWidget(self.copy_btn)
        
        bottom_layout.addLayout(share_row)
        layout.addWidget(bottom_section)
    
    def _set_placeholder(self):
        """Set a placeholder while thumbnail loads."""
        self.thumb_label.setText("🖼️")
        self.thumb_label.setStyleSheet(f"""
            font-size: 48px;
            background: transparent;
            color: {styles.COLORS['text_light']};
        """)
    
    def set_thumbnail(self, pixmap: QPixmap):
        """Set the loaded thumbnail image."""
        self._pixmap = pixmap
        
        # Scale to fill card width while staying within the image container height
        scaled = pixmap.scaled(
            self.CARD_WIDTH,
            self.THUMB_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.thumb_label.setPixmap(scaled)
        self.thumb_label.setStyleSheet("background: transparent;")
        
        # Image container is fixed height; image is centred inside it
    
    def _on_sharecode_edited(self):
        """Handle sharecode editing completion."""
        new_value = self.share_edit.text().strip()
        old_value = self._image_data.get('share_string', '')
        
        if new_value != old_value:
            self._image_data['share_string'] = new_value
            self.sharelink_changed.emit(self._image_id, new_value)
            # Update copy button state
            self.copy_btn.setEnabled(bool(new_value))
    
    def _copy_share_string(self):
        """Copy share string to clipboard."""
        share_text = self.share_edit.text().strip()
        if share_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(share_text)
            
            # Visual feedback - change to tick icon and success color
            self.copy_btn.setIcon(self.tick_icon)
            self.copy_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {styles.COLORS['success']};
                    border: none;
                    border-radius: 8px;
                }}
            """)
            
            # Reset after 1 second
            from PyQt6.QtCore import QTimer
            def reset_style():
                self.copy_btn.setIcon(self.copy_icon_normal)
                self.copy_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #f1f5f9;
                        border: none;
                        border-radius: 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {styles.COLORS['primary']};
                    }}
                    QPushButton:disabled {{
                        background-color: #e2e8f0;
                        opacity: 0.5;
                    }}
                """)
            QTimer.singleShot(200, reset_style)
    
    def eventFilter(self, obj, event):
        """Handle events for child widgets, specifically copy button hover."""
        if obj == self.copy_btn:
            if event.type() == QEvent.Type.Enter:
                # Mouse entered button - change to white icon
                self.copy_btn.setIcon(self.copy_icon_hover)
            elif event.type() == QEvent.Type.Leave:
                # Mouse left button - change back to normal icon
                self.copy_btn.setIcon(self.copy_icon_normal)
        return super().eventFilter(obj, event)
    
    def enterEvent(self, event):
        """Handle mouse enter - show hover effect."""
        self._is_hovered = True
        
        # Update shadow on hover
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(190, 90, 141, 40))  # Primary color shadow
        self.setGraphicsEffect(shadow)
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave - reset hover effect."""
        self._is_hovered = False
        
        # Reset shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 25))
        self.setGraphicsEffect(shadow)
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press."""
        # Don't emit click if clicking on input or button
        child = self.childAt(event.pos())
        if isinstance(child, (QLineEdit, QPushButton)):
            super().mousePressEvent(event)
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._image_id)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click for editing."""
        # Don't emit double-click if clicking on input or button
        child = self.childAt(event.pos())
        if isinstance(child, (QLineEdit, QPushButton)):
            super().mouseDoubleClickEvent(event)
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self._image_id)
        super().mouseDoubleClickEvent(event)
    
    @property
    def image_id(self) -> str:
        return self._image_id
    
    @property
    def image_data(self) -> dict:
        return self._image_data
    
    def update_data(self, new_data: dict):
        """Update the displayed data."""
        self._image_data = new_data
        
        # Update share string
        share_text = new_data.get('share_string', '')
        self.share_edit.setText(share_text)
        self.copy_btn.setEnabled(bool(share_text))

    def refresh_theme(self):
        self.setStyleSheet(f"""
            ThumbnailWidget {{
                background-color: {styles.COLORS['card_light']};
                border-radius: {styles.RADIUS['xl']};
            }}
            ThumbnailWidget:hover {{
                background-color: {styles.COLORS['sidebar_light']};
            }}
        """)
        # Rest mostly rely on being recreated anyway during _load_images

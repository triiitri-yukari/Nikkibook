"""
Dialog components for NikkiBook.
Modern styled dialogs for adding/editing images, categories, and subcategories.
All user-visible text is sourced from the i18n module so language can change at runtime.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QFileDialog,
    QMessageBox, QDialogButtonBox, QFrame, QGraphicsDropShadowEffect,
    QApplication
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor, QIntValidator
from typing import Optional, List, Tuple

from .styles import (
    COLORS, FONTS, PRIMARY_BUTTON_STYLE, DELETE_BUTTON_STYLE,
    FORM_LABEL_STYLE
)
from .icons import icon as ui_icon, pixmap as ui_pixmap, icon_size
from .. import i18n as _i18n
from ..config import (
    SNAP_CAPTURE_DEFAULT_OFFSET_X,
    SNAP_CAPTURE_DEFAULT_SIZE,
    SNAP_CAPTURE_MAX_DIMENSION,
)


def t(key: str, **kw) -> str:
    return _i18n.t(key, **kw)


# Common dialog styles
DIALOG_STYLE = f"""
    QDialog {{
        background-color: {COLORS['sidebar_light']};
        border-radius: 16px;
    }}
"""

DIALOG_INPUT_STYLE = f"""
    QLineEdit {{
        background-color: rgba(190, 90, 141, 0.15);
        border: 1px solid rgba(190, 90, 141, 0.3);
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 13px;
        color: {COLORS['text_dark']};
    }}
    QLineEdit:focus {{
        border: 2px solid {COLORS['primary']};
        background-color: {COLORS['card_light']};
    }}
"""

DIALOG_COMBO_STYLE = f"""
    QComboBox {{
        background-color: rgba(190, 90, 141, 0.15);
        border: 1px solid rgba(190, 90, 141, 0.3);
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 13px;
        color: {COLORS['text_dark']};
    }}
    QComboBox:focus {{
        border: 2px solid {COLORS['primary']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLORS['card_light']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        selection-background-color: {COLORS['primary']};
        selection-color: white;
    }}
"""

DIALOG_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {COLORS['primary_hover']};
    }}
"""

DIALOG_CANCEL_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: transparent;
        color: {COLORS['text_medium']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 13px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: rgba(0, 0, 0, 0.05);
    }}
"""


# ---------------------------------------------------------------------------
# Helper – connect a dialog to language change events
# ---------------------------------------------------------------------------
def _connect_retranslate(dialog: QDialog, retranslate_fn):
    """Wire up dialog to retranslate when global language changes."""
    mgr = _i18n.get_manager()
    mgr.language_changed.connect(retranslate_fn)
    # Disconnect on dialog close so we don't leak
    dialog.finished.connect(lambda: mgr.language_changed.disconnect(retranslate_fn))


# ---------------------------------------------------------------------------
# AddCategoryDialog
# ---------------------------------------------------------------------------
class AddCategoryDialog(QDialog):
    """Modern dialog for creating a new category."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(400)
        self.setStyleSheet(DIALOG_STYLE)
        self._setup_ui()
        self._retranslate()
        _connect_retranslate(self, self._retranslate)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        self._title_lbl = QLabel()
        self._title_lbl.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS['text_dark']};
            background-color: transparent;
            border: none;
            padding: 0;
        """)
        layout.addWidget(self._title_lbl)

        name_container = QVBoxLayout()
        name_container.setSpacing(6)

        self._name_lbl = QLabel()
        self._name_lbl.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 700;
            color: {COLORS['text_light']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background-color: transparent;
            border: none;
        """)
        name_container.addWidget(self._name_lbl)

        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(DIALOG_INPUT_STYLE)
        self.name_edit.returnPressed.connect(self._validate_and_accept)
        name_container.addWidget(self.name_edit)

        layout.addLayout(name_container)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._cancel_btn = QPushButton()
        self._cancel_btn.setStyleSheet(DIALOG_CANCEL_BUTTON_STYLE)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._ok_btn = QPushButton()
        self._ok_btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        self._ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ok_btn.setDefault(True)
        self._ok_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(self._ok_btn)

        layout.addLayout(btn_layout)

    def _retranslate(self):
        self.setWindowTitle(t("add_category_title"))
        self._title_lbl.setText(t("add_category_title"))
        self._name_lbl.setText(t("category_name_label"))
        self.name_edit.setPlaceholderText(t("category_name_placeholder"))
        self._cancel_btn.setText(t("cancel"))
        self._ok_btn.setText(t("create_category_btn"))

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, t("validation_error_title"), t("validation_name_empty"))
            return
        self.accept()

    def get_name(self) -> str:
        return self.name_edit.text().strip()


# ---------------------------------------------------------------------------
# AddSubcategoryDialog
# ---------------------------------------------------------------------------
class AddSubcategoryDialog(QDialog):
    """Modern dialog for creating a new subcategory."""

    def __init__(self, categories: List[Tuple[str, str]], parent=None, preselect_category_id: str = None):
        super().__init__(parent)
        self.setFixedWidth(400)
        self.setStyleSheet(DIALOG_STYLE)
        self._categories = categories
        self._preselect = preselect_category_id
        self._setup_ui()
        self._retranslate()
        _connect_retranslate(self, self._retranslate)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        self._title_lbl = QLabel()
        self._title_lbl.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS['text_dark']};
            background-color: transparent;
            border: none;
            padding: 0;
        """)
        layout.addWidget(self._title_lbl)

        cat_container = QVBoxLayout()
        cat_container.setSpacing(6)

        self._cat_lbl = QLabel()
        self._cat_lbl.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 700;
            color: {COLORS['text_light']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background-color: transparent;
            border: none;
        """)
        cat_container.addWidget(self._cat_lbl)

        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(DIALOG_COMBO_STYLE)
        for cat_id, cat_name in self._categories:
            self.category_combo.addItem(cat_name, cat_id)

        if self._preselect:
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == self._preselect:
                    self.category_combo.setCurrentIndex(i)
                    break

        cat_container.addWidget(self.category_combo)
        layout.addLayout(cat_container)

        name_container = QVBoxLayout()
        name_container.setSpacing(6)

        self._name_lbl = QLabel()
        self._name_lbl.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 700;
            color: {COLORS['text_light']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background-color: transparent;
            border: none;
        """)
        name_container.addWidget(self._name_lbl)

        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(DIALOG_INPUT_STYLE)
        name_container.addWidget(self.name_edit)

        layout.addLayout(name_container)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._cancel_btn = QPushButton()
        self._cancel_btn.setStyleSheet(DIALOG_CANCEL_BUTTON_STYLE)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._ok_btn = QPushButton()
        self._ok_btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        self._ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ok_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(self._ok_btn)

        layout.addLayout(btn_layout)

    def _retranslate(self):
        self.setWindowTitle(t("add_subcategory_title"))
        self._title_lbl.setText(t("add_subcategory_title"))
        self._cat_lbl.setText(t("parent_category_label"))
        self._name_lbl.setText(t("subcategory_name_label"))
        self.name_edit.setPlaceholderText(t("subcategory_name_placeholder"))
        self._cancel_btn.setText(t("cancel"))
        self._ok_btn.setText(t("create_subcategory_btn"))

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, t("validation_error_title"), t("validation_subname_empty"))
            return
        if self.category_combo.currentIndex() < 0:
            QMessageBox.warning(self, t("validation_error_title"), t("validation_select_category"))
            return
        self.accept()

    def get_category_id(self) -> str:
        return self.category_combo.currentData()

    def get_name(self) -> str:
        return self.name_edit.text().strip()


# ---------------------------------------------------------------------------
# AddImageDialog
# ---------------------------------------------------------------------------
class AddImageDialog(QDialog):
    """Modern dialog for adding a new image with file selection."""

    def __init__(
        self,
        categories: List[Tuple[str, str]],
        subcategories: List[Tuple[str, str, str]],
        parent=None,
        preselect_category_id: str = None,
        preselect_subcategory_id: str = None
    ):
        super().__init__(parent)
        self.setFixedWidth(500)
        self.setStyleSheet(DIALOG_STYLE)
        self._categories = categories
        self._subcategories = subcategories
        self._preselect_cat = preselect_category_id
        self._preselect_subcat = preselect_subcategory_id
        self._selected_file: Optional[str] = None
        self._setup_ui()
        self._retranslate()
        _connect_retranslate(self, self._retranslate)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        self._title_lbl = QLabel()
        self._title_lbl.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS['text_dark']};
            background-color: transparent;
            border: none;
            padding: 0;
        """)
        layout.addWidget(self._title_lbl)

        # File selection
        file_container = QVBoxLayout()
        file_container.setSpacing(6)

        self._file_section_lbl = QLabel()
        self._file_section_lbl.setStyleSheet(FORM_LABEL_STYLE)
        file_container.addWidget(self._file_section_lbl)

        file_row = QHBoxLayout()
        file_row.setSpacing(12)

        self.file_label = QLineEdit()
        self.file_label.setReadOnly(True)
        self.file_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.file_label.setStyleSheet(DIALOG_INPUT_STYLE)
        self.file_label.setFixedHeight(44)
        file_row.addWidget(self.file_label, 1)

        self._browse_btn = QPushButton()
        self._browse_btn.setIcon(ui_icon("folder", COLORS['primary'], 18))
        self._browse_btn.setIconSize(icon_size(18))
        self._browse_btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        self._browse_btn.setFixedHeight(44)
        self._browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(self._browse_btn)

        file_container.addLayout(file_row)
        layout.addLayout(file_container)

        # Name field
        name_container = QVBoxLayout()
        name_container.setSpacing(6)

        self._name_lbl = QLabel()
        self._name_lbl.setStyleSheet(FORM_LABEL_STYLE)
        name_container.addWidget(self._name_lbl)

        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(DIALOG_INPUT_STYLE)
        name_container.addWidget(self.name_edit)

        layout.addLayout(name_container)

        # Category / Subcategory row
        cat_row = QHBoxLayout()
        cat_row.setSpacing(16)

        cat_container = QVBoxLayout()
        cat_container.setSpacing(6)

        self._cat_lbl = QLabel()
        self._cat_lbl.setStyleSheet(FORM_LABEL_STYLE)
        cat_container.addWidget(self._cat_lbl)

        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(DIALOG_COMBO_STYLE)
        for cat_id, cat_name in self._categories:
            self.category_combo.addItem(cat_name, cat_id)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        cat_container.addWidget(self.category_combo)

        cat_row.addLayout(cat_container, 1)

        subcat_container = QVBoxLayout()
        subcat_container.setSpacing(6)

        self._subcat_lbl = QLabel()
        self._subcat_lbl.setStyleSheet(FORM_LABEL_STYLE)
        subcat_container.addWidget(self._subcat_lbl)

        self.subcategory_combo = QComboBox()
        self.subcategory_combo.setStyleSheet(DIALOG_COMBO_STYLE)
        subcat_container.addWidget(self.subcategory_combo)

        cat_row.addLayout(subcat_container, 1)
        layout.addLayout(cat_row)

        if self._preselect_cat:
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == self._preselect_cat:
                    self.category_combo.setCurrentIndex(i)
                    break
        else:
            self._on_category_changed(0)

        if self._preselect_subcat:
            for i in range(self.subcategory_combo.count()):
                if self.subcategory_combo.itemData(i) == self._preselect_subcat:
                    self.subcategory_combo.setCurrentIndex(i)
                    break

        # Share string
        share_container = QVBoxLayout()
        share_container.setSpacing(6)

        self._share_lbl = QLabel()
        self._share_lbl.setStyleSheet(FORM_LABEL_STYLE)
        share_container.addWidget(self._share_lbl)

        self.share_edit = QLineEdit()
        self.share_edit.setStyleSheet(DIALOG_INPUT_STYLE)
        share_container.addWidget(self.share_edit)

        layout.addLayout(share_container)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._cancel_btn = QPushButton()
        self._cancel_btn.setStyleSheet(DIALOG_CANCEL_BUTTON_STYLE)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._ok_btn = QPushButton()
        self._ok_btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        self._ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ok_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(self._ok_btn)

        layout.addLayout(btn_layout)

    def _retranslate(self):
        self.setWindowTitle(t("add_image_title"))
        self._title_lbl.setText(t("add_image_title"))
        self._file_section_lbl.setText(t("select_file_label"))
        if not self._selected_file:
            self.file_label.clear()
            self.file_label.setPlaceholderText(t("no_file_selected"))
        self._browse_btn.setText(t("browse_btn"))
        self._name_lbl.setText(t("display_name_label"))
        self.name_edit.setPlaceholderText(t("display_name_placeholder"))
        self._cat_lbl.setText(t("category_label"))
        self._subcat_lbl.setText(t("subcategory_label"))
        # Update (None) item text in subcategory combo
        for i in range(self.subcategory_combo.count()):
            if self.subcategory_combo.itemData(i) is None:
                self.subcategory_combo.setItemText(i, t("none_option"))
        self._share_lbl.setText(t("sharecode_label"))
        self.share_edit.setPlaceholderText(t("sharecode_placeholder"))
        self._cancel_btn.setText(t("cancel"))
        self._ok_btn.setText(t("add_image_ok_btn"))

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t("select_file_label"),
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tiff *.tif)"
        )
        if file_path:
            self._selected_file = file_path
            from pathlib import Path
            self.file_label.setText(Path(file_path).name)
            self.file_label.setCursorPosition(0)
            self.file_label.setToolTip(file_path)

    def _on_category_changed(self, index: int):
        self.subcategory_combo.clear()
        self.subcategory_combo.addItem(t("none_option"), None)

        category_id = self.category_combo.currentData()
        if category_id:
            for sub_id, sub_name, cat_id in self._subcategories:
                if cat_id == category_id:
                    self.subcategory_combo.addItem(sub_name, sub_id)

    def _validate_and_accept(self):
        if not self._selected_file:
            QMessageBox.warning(self, t("validation_error_title"), t("validation_select_file"))
            return
        if self.category_combo.currentIndex() < 0:
            QMessageBox.warning(self, t("validation_error_title"), t("validation_select_image_category"))
            return
        self.accept()

    def get_file_path(self) -> str:
        return self._selected_file

    def get_name(self) -> Optional[str]:
        name = self.name_edit.text().strip()
        return name if name else None

    def get_category_id(self) -> str:
        return self.category_combo.currentData()

    def get_subcategory_id(self) -> Optional[str]:
        return self.subcategory_combo.currentData()

    def get_share_string(self) -> str:
        return self.share_edit.text().strip()


# ---------------------------------------------------------------------------
# EditImageDialog
# ---------------------------------------------------------------------------
class EditImageDialog(QDialog):
    """Modern dialog for editing an existing image's metadata."""

    def __init__(
        self,
        image_data: dict,
        categories: List[Tuple[str, str]],
        subcategories: List[Tuple[str, str, str]],
        parent=None
    ):
        super().__init__(parent)
        self.setFixedWidth(500)
        self.setStyleSheet(DIALOG_STYLE)
        self._image = image_data
        self._categories = categories
        self._subcategories = subcategories
        self._setup_ui()
        self._retranslate()
        _connect_retranslate(self, self._retranslate)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        self._title_lbl = QLabel()
        self._title_lbl.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS['text_dark']};
            background-color: transparent;
            border: none;
            padding: 0;
        """)
        layout.addWidget(self._title_lbl)

        filename_row = QHBoxLayout()
        filename_row.setSpacing(8)

        filename_icon = QLabel()
        filename_icon.setPixmap(ui_pixmap("file-image", COLORS['primary'], 18))
        filename_icon.setFixedSize(20, 20)
        filename_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filename_row.addWidget(filename_icon)

        filename_label = QLabel(self._image.get('original_filename') or self._image['filename'])
        filename_label.setStyleSheet(f"color: {COLORS['primary']}; font-size: 13px;")
        filename_row.addWidget(filename_label, 1)
        layout.addLayout(filename_row)

        name_container = QVBoxLayout()
        name_container.setSpacing(6)

        self._name_lbl = QLabel()
        self._name_lbl.setStyleSheet(FORM_LABEL_STYLE)
        name_container.addWidget(self._name_lbl)

        self.name_edit = QLineEdit()
        self.name_edit.setText(self._image.get('name') or '')
        self.name_edit.setStyleSheet(DIALOG_INPUT_STYLE)
        name_container.addWidget(self.name_edit)

        layout.addLayout(name_container)

        cat_row = QHBoxLayout()
        cat_row.setSpacing(16)

        cat_container = QVBoxLayout()
        cat_container.setSpacing(6)

        self._cat_lbl = QLabel()
        self._cat_lbl.setStyleSheet(FORM_LABEL_STYLE)
        cat_container.addWidget(self._cat_lbl)

        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(DIALOG_COMBO_STYLE)
        for cat_id, cat_name in self._categories:
            self.category_combo.addItem(cat_name, cat_id)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        cat_container.addWidget(self.category_combo)

        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == self._image['category_id']:
                self.category_combo.setCurrentIndex(i)
                break

        cat_row.addLayout(cat_container, 1)

        subcat_container = QVBoxLayout()
        subcat_container.setSpacing(6)

        self._subcat_lbl = QLabel()
        self._subcat_lbl.setStyleSheet(FORM_LABEL_STYLE)
        subcat_container.addWidget(self._subcat_lbl)

        self.subcategory_combo = QComboBox()
        self.subcategory_combo.setStyleSheet(DIALOG_COMBO_STYLE)
        subcat_container.addWidget(self.subcategory_combo)

        cat_row.addLayout(subcat_container, 1)
        layout.addLayout(cat_row)

        self._on_category_changed(self.category_combo.currentIndex())
        if self._image.get('subcategory_id'):
            for i in range(self.subcategory_combo.count()):
                if self.subcategory_combo.itemData(i) == self._image['subcategory_id']:
                    self.subcategory_combo.setCurrentIndex(i)
                    break

        share_container = QVBoxLayout()
        share_container.setSpacing(6)

        self._share_lbl = QLabel()
        self._share_lbl.setStyleSheet(FORM_LABEL_STYLE)
        share_container.addWidget(self._share_lbl)

        self.share_edit = QLineEdit()
        self.share_edit.setText(self._image.get('share_string') or '')
        self.share_edit.setStyleSheet(DIALOG_INPUT_STYLE)
        share_container.addWidget(self.share_edit)

        layout.addLayout(share_container)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._cancel_btn = QPushButton()
        self._cancel_btn.setStyleSheet(DIALOG_CANCEL_BUTTON_STYLE)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._ok_btn = QPushButton()
        self._ok_btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        self._ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self._ok_btn)

        layout.addLayout(btn_layout)

    def _retranslate(self):
        self.setWindowTitle(t("edit_image_title"))
        self._title_lbl.setText(t("edit_image_title"))
        self._name_lbl.setText(t("display_name_label_required"))
        self.name_edit.setPlaceholderText(t("display_name_placeholder"))
        self._cat_lbl.setText(t("category_label"))
        self._subcat_lbl.setText(t("subcategory_label"))
        for i in range(self.subcategory_combo.count()):
            if self.subcategory_combo.itemData(i) is None:
                self.subcategory_combo.setItemText(i, t("none_option"))
        self._share_lbl.setText(t("sharecode_label_required"))
        self.share_edit.setPlaceholderText(t("sharecode_placeholder"))
        self._cancel_btn.setText(t("cancel"))
        self._ok_btn.setText(t("save_changes_btn"))

    def _on_category_changed(self, index: int):
        self.subcategory_combo.clear()
        self.subcategory_combo.addItem(t("none_option"), None)

        category_id = self.category_combo.currentData()
        if category_id:
            for sub_id, sub_name, cat_id in self._subcategories:
                if cat_id == category_id:
                    self.subcategory_combo.addItem(sub_name, sub_id)

    def get_name(self) -> Optional[str]:
        name = self.name_edit.text().strip()
        return name if name else None

    def get_category_id(self) -> str:
        return self.category_combo.currentData()

    def get_subcategory_id(self) -> Optional[str]:
        return self.subcategory_combo.currentData()

    def get_share_string(self) -> str:
        return self.share_edit.text().strip()


# ---------------------------------------------------------------------------
# RenameDialog
# ---------------------------------------------------------------------------
class RenameDialog(QDialog):
    """Modern dialog for renaming categories/subcategories."""

    def __init__(self, title: str, current_name: str, parent=None):
        super().__init__(parent)
        self._dialog_title = title
        self.setFixedWidth(400)
        self.setStyleSheet(DIALOG_STYLE)
        self._setup_ui(current_name)
        self._retranslate()
        _connect_retranslate(self, self._retranslate)

    def _setup_ui(self, current_name: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        self._title_lbl = QLabel(self._dialog_title)
        self._title_lbl.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS['text_dark']};
            background-color: transparent;
            border: none;
            padding: 0;
        """)
        layout.addWidget(self._title_lbl)

        name_container = QVBoxLayout()
        name_container.setSpacing(6)

        self._name_lbl = QLabel()
        self._name_lbl.setStyleSheet(FORM_LABEL_STYLE)
        name_container.addWidget(self._name_lbl)

        self.name_edit = QLineEdit()
        self.name_edit.setText(current_name)
        self.name_edit.selectAll()
        self.name_edit.setStyleSheet(DIALOG_INPUT_STYLE)
        self.name_edit.returnPressed.connect(self._validate_and_accept)
        name_container.addWidget(self.name_edit)

        layout.addLayout(name_container)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._cancel_btn = QPushButton()
        self._cancel_btn.setStyleSheet(DIALOG_CANCEL_BUTTON_STYLE)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._ok_btn = QPushButton()
        self._ok_btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        self._ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ok_btn.setDefault(True)
        self._ok_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(self._ok_btn)

        layout.addLayout(btn_layout)

    def _retranslate(self):
        self.setWindowTitle(self._dialog_title)
        self._name_lbl.setText(t("new_name_label"))
        self._cancel_btn.setText(t("cancel"))
        self._ok_btn.setText(t("rename_btn"))

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, t("validation_error_title"), t("validation_name_cannot_be_empty"))
            return
        self.accept()

    def get_name(self) -> str:
        return self.name_edit.text().strip()


# ---------------------------------------------------------------------------
# SnapProgressDialog
# ---------------------------------------------------------------------------
class SnapProgressDialog(QDialog):
    """Progress dialog shown during the snap automation workflow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(420, 210)
        self.setStyleSheet(DIALOG_STYLE)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self._cancelled = False
        self._current_step = 0
        self._setup_ui()
        self._retranslate()
        _connect_retranslate(self, self._retranslate)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self._title_icon = QLabel()
        self._title_icon.setPixmap(ui_pixmap("camera", COLORS['primary'], 20))
        self._title_icon.setFixedSize(22, 22)
        self._title_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_icon.setStyleSheet("background: transparent; border: none;")
        title_row.addWidget(self._title_icon)

        self._title_lbl = QLabel()
        self._title_lbl.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {COLORS['text_dark']};
            background-color: transparent;
            border: none;
        """)
        title_row.addWidget(self._title_lbl, 1)
        layout.addLayout(title_row)

        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_medium']};
            background-color: transparent;
            border: none;
        """)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.step_label = QLabel()
        self.step_label.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_light']};
            font-weight: 500;
            background-color: transparent;
            border: none;
        """)
        layout.addWidget(self.step_label)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton()
        self._cancel_btn.setStyleSheet(DIALOG_CANCEL_BUTTON_STYLE)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self._cancel_btn)

        layout.addLayout(btn_layout)

    def _retranslate(self):
        self.setWindowTitle(t("snap_window_title"))
        self._title_lbl.setText(t("snap_title"))
        if not self.status_label.text():
            self.status_label.setText(t("snap_initializing"))
        self.step_label.setText(t("snap_step", step=self._current_step))
        self._cancel_btn.setText(t("cancel"))

    def showEvent(self, event):
        super().showEvent(event)
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            margin = 20
            x = screen_geo.left() + margin
            y = screen_geo.bottom() - self.height() - margin
            self.move(x, y)

    def update_progress(self, step: int, description: str):
        self._current_step = step
        self.step_label.setText(t("snap_step", step=step))
        self.status_label.setText(description)

    def _on_cancel(self):
        self._cancelled = True
        self.reject()

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled


# ---------------------------------------------------------------------------
# SettingsDialog – now includes language picker
# ---------------------------------------------------------------------------
class SettingsDialog(QDialog):
    """Dialog for configuring application settings (Snap Mode + Language)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(440)
        self.setStyleSheet(DIALOG_STYLE)
        self.settings = QSettings("NikkiBook", "App")
        self._setup_ui()
        self._retranslate()
        _connect_retranslate(self, self._retranslate)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        self._title_lbl = QLabel()
        self._title_lbl.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS['text_dark']};
            background-color: transparent;
            border: none;
            padding: 0;
        """)
        layout.addWidget(self._title_lbl)

        # --------------- Language ---------------
        lang_layout = QVBoxLayout()
        lang_layout.setSpacing(8)

        self._lang_lbl = QLabel()
        self._lang_lbl.setStyleSheet("font-size: 14px; color: #555555; background: transparent;")
        lang_layout.addWidget(self._lang_lbl)

        self.lang_combo = QComboBox()
        self.lang_combo.setStyleSheet(DIALOG_COMBO_STYLE)
        for code, name in _i18n.LANGUAGE_NAMES.items():
            self.lang_combo.addItem(name, code)

        # Select current language
        current_lang = _i18n.get_manager().language
        idx_lang = self.lang_combo.findData(current_lang)
        if idx_lang >= 0:
            self.lang_combo.setCurrentIndex(idx_lang)

        # Live preview: change language immediately on combo change
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # --------------- Snap Mode ---------------
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(8)

        self._mode_lbl = QLabel()
        self._mode_lbl.setStyleSheet("font-size: 14px; color: #555555; background: transparent;")
        mode_layout.addWidget(self._mode_lbl)

        self.mode_combo = QComboBox()
        self.mode_combo.setStyleSheet(DIALOG_COMBO_STYLE)

        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)

        # --------------- Capture Area ---------------
        area_layout = QVBoxLayout()
        area_layout.setSpacing(8)

        self._area_lbl = QLabel()
        self._area_lbl.setStyleSheet("font-size: 14px; color: #555555; background: transparent;")
        area_layout.addWidget(self._area_lbl)

        custom_dimensions_layout = QHBoxLayout()
        custom_dimensions_layout.setSpacing(12)

        width_layout = QVBoxLayout()
        width_layout.setSpacing(6)
        self._capture_width_lbl = QLabel()
        self._capture_width_lbl.setStyleSheet(
            "font-size: 12px; color: #777777; background: transparent;"
        )
        self.capture_width_edit = QLineEdit()
        self.capture_width_edit.setValidator(
            QIntValidator(1, SNAP_CAPTURE_MAX_DIMENSION, self)
        )
        self.capture_width_edit.setPlaceholderText(
            str(SNAP_CAPTURE_DEFAULT_SIZE[0])
        )
        self.capture_width_edit.setStyleSheet(DIALOG_INPUT_STYLE)
        saved_width = self.settings.value("snap_capture_width", "")
        if saved_width and str(saved_width) != str(SNAP_CAPTURE_DEFAULT_SIZE[0]):
            self.capture_width_edit.setText(str(saved_width))
        width_layout.addWidget(self._capture_width_lbl)
        width_layout.addWidget(self.capture_width_edit)
        custom_dimensions_layout.addLayout(width_layout)

        height_layout = QVBoxLayout()
        height_layout.setSpacing(6)
        self._capture_height_lbl = QLabel()
        self._capture_height_lbl.setStyleSheet(
            "font-size: 12px; color: #777777; background: transparent;"
        )
        self.capture_height_edit = QLineEdit()
        self.capture_height_edit.setValidator(
            QIntValidator(1, SNAP_CAPTURE_MAX_DIMENSION, self)
        )
        self.capture_height_edit.setPlaceholderText(
            str(SNAP_CAPTURE_DEFAULT_SIZE[1])
        )
        self.capture_height_edit.setStyleSheet(DIALOG_INPUT_STYLE)
        saved_height = self.settings.value("snap_capture_height", "")
        if saved_height and str(saved_height) != str(SNAP_CAPTURE_DEFAULT_SIZE[1]):
            self.capture_height_edit.setText(str(saved_height))
        height_layout.addWidget(self._capture_height_lbl)
        height_layout.addWidget(self.capture_height_edit)
        custom_dimensions_layout.addLayout(height_layout)

        offset_layout = QVBoxLayout()
        offset_layout.setSpacing(6)
        self._capture_offset_lbl = QLabel()
        self._capture_offset_lbl.setStyleSheet(
            "font-size: 12px; color: #777777; background: transparent;"
        )
        self.capture_offset_edit = QLineEdit()
        self.capture_offset_edit.setValidator(
            QIntValidator(0, SNAP_CAPTURE_MAX_DIMENSION, self)
        )
        self.capture_offset_edit.setPlaceholderText(
            str(SNAP_CAPTURE_DEFAULT_OFFSET_X)
        )
        self.capture_offset_edit.setStyleSheet(DIALOG_INPUT_STYLE)
        saved_offset = self.settings.value("snap_capture_offset_x", "")
        if (saved_offset not in ("", None)
                and str(saved_offset) != str(SNAP_CAPTURE_DEFAULT_OFFSET_X)):
            self.capture_offset_edit.setText(str(saved_offset))
        offset_layout.addWidget(self._capture_offset_lbl)
        offset_layout.addWidget(self.capture_offset_edit)
        custom_dimensions_layout.addLayout(offset_layout)

        area_layout.addLayout(custom_dimensions_layout)
        self._capture_default_lbl = QLabel()
        self._capture_default_lbl.setStyleSheet(
            "font-size: 11px; color: #777777; background: transparent;"
        )
        area_layout.addWidget(self._capture_default_lbl)
        layout.addLayout(area_layout)

        # --------------- Snap Visibility ---------------
        snap_vis_layout = QVBoxLayout()
        snap_vis_layout.setSpacing(8)

        self._snap_vis_lbl = QLabel()
        self._snap_vis_lbl.setStyleSheet("font-size: 14px; color: #555555; background: transparent;")
        snap_vis_layout.addWidget(self._snap_vis_lbl)

        self.snap_vis_combo = QComboBox()
        self.snap_vis_combo.setStyleSheet(DIALOG_COMBO_STYLE)

        current_vis = self.settings.value("snap_button_visible", "show")
        # items populated in _retranslate
        snap_vis_layout.addWidget(self.snap_vis_combo)
        layout.addLayout(snap_vis_layout)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._cancel_btn = QPushButton()
        self._cancel_btn.setStyleSheet(DIALOG_CANCEL_BUTTON_STYLE)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._save_btn = QPushButton()
        self._save_btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._save_and_accept)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

        # --------------- Footnote ---------------
        footnote_layout = QVBoxLayout()
        footnote_layout.setSpacing(2)
        footnote_layout.setContentsMargins(0, 15, 0, 0)
        
        self._author_lbl = QLabel()
        self._author_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._author_lbl.setStyleSheet(f"font-size: 11px; color: #555555; background: transparent;")
        
        self._coffee_lbl = QLabel()
        self._coffee_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._coffee_lbl.setOpenExternalLinks(True)
        self._coffee_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['primary']}; background: transparent;")
        
        footnote_layout.addWidget(self._author_lbl)
        footnote_layout.addWidget(self._coffee_lbl)
        layout.addLayout(footnote_layout)

    def _retranslate(self):
        self.setWindowTitle(t("settings_title"))
        self._title_lbl.setText(t("settings_title"))
        self._lang_lbl.setText(t("language_label"))
        self._mode_lbl.setText(t("snap_mode_label"))
        # Rebuild mode combo items with translated text (preserve selection)
        current_mode_data = self.mode_combo.currentData() or self.settings.value("snap_mode", "album")
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        self.mode_combo.addItem(t("snap_mode_album"), "album")
        self.mode_combo.addItem(t("snap_mode_nikkibook"), "nikkibook_only")
        idx = self.mode_combo.findData(current_mode_data)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        self.mode_combo.blockSignals(False)
        self._area_lbl.setText(t("capture_area_label"))
        self._capture_width_lbl.setText(t("capture_width_label"))
        self._capture_height_lbl.setText(t("capture_height_label"))
        self._capture_offset_lbl.setText(t("capture_offset_label"))
        self._capture_default_lbl.setText(t("capture_default_hint"))
        self._snap_vis_lbl.setText(t("snap_visibility_label"))
        # Rebuild snap visibility combo
        current_vis_data = self.snap_vis_combo.currentData() or self.settings.value("snap_button_visible", "show")
        self.snap_vis_combo.blockSignals(True)
        self.snap_vis_combo.clear()
        self.snap_vis_combo.addItem(t("snap_visible"), "show")
        self.snap_vis_combo.addItem(t("snap_hidden"), "hide")
        idx_v = self.snap_vis_combo.findData(current_vis_data)
        if idx_v >= 0:
            self.snap_vis_combo.setCurrentIndex(idx_v)
        self.snap_vis_combo.blockSignals(False)
        self._author_lbl.setText(t("settings_footnote_author"))
        
        coffee_url = t("settings_footnote_coffee")
        self._coffee_lbl.setText(f'<a href="{coffee_url}" style="color: {COLORS["primary"]}; text-decoration: none;">{coffee_url}</a>')
        
        self._cancel_btn.setText(t("cancel"))
        self._save_btn.setText(t("save"))

    def _on_language_changed(self, index: int):
        """Immediately apply the selected language for live preview."""
        lang_code = self.lang_combo.itemData(index)
        if lang_code:
            _i18n.get_manager().set_language(lang_code)

    def _save_and_accept(self):
        mode = self.mode_combo.currentData()
        lang = self.lang_combo.currentData()
        snap_vis = self.snap_vis_combo.currentData()
        self.settings.setValue("snap_mode", mode)
        self.settings.remove("snap_capture_area")
        width = self.capture_width_edit.text().strip()
        height = self.capture_height_edit.text().strip()
        offset = self.capture_offset_edit.text().strip()
        if width:
            self.settings.setValue("snap_capture_width", int(width))
        else:
            self.settings.remove("snap_capture_width")
        if height:
            self.settings.setValue("snap_capture_height", int(height))
        else:
            self.settings.remove("snap_capture_height")
        if offset:
            self.settings.setValue("snap_capture_offset_x", int(offset))
        else:
            self.settings.remove("snap_capture_offset_x")
        self.settings.setValue("snap_button_visible", snap_vis)
        # Language is already applied live; just persist it
        _i18n.get_manager().set_language(lang)
        self.accept()


# ---------------------------------------------------------------------------
# Standalone helper functions
# ---------------------------------------------------------------------------
def show_error(parent, title: str, message: str):
    """Display an error dialog."""
    QMessageBox.critical(parent, title, message)


def show_warning(parent, title: str, message: str):
    """Display a warning dialog."""
    QMessageBox.warning(parent, title, message)


def confirm_delete(parent, item_type: str, item_name: str) -> bool:
    """Show a confirmation dialog for deletion. Returns True if confirmed."""
    result = QMessageBox.question(
        parent,
        t("confirm_delete_title", item_type=item_type),
        t("confirm_delete_msg", item_name=item_name),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    return result == QMessageBox.StandardButton.Yes

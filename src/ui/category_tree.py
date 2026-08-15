"""
Category tree sidebar for NikkiBook.
Modern design with folder icons, counts, and collapsible tree structure.
Matches the reference design from ref image_catalog_dashboard.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget,
    QTreeWidgetItem, QMenu, QSizePolicy, QLabel, QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction, QColor, QPainter
from typing import Optional, Dict, List
import uuid
from datetime import datetime

from .. import database
from .dialogs import AddCategoryDialog, AddSubcategoryDialog, RenameDialog, confirm_delete, show_error
from .icons import icon as ui_icon, icon_size
import src.ui.styles as styles
from .. import i18n as _i18n


def t(key: str, **kw) -> str:
    return _i18n.t(key, **kw)


class CategoryTreeItemDelegate(QStyledItemDelegate):
    """Paint selection only across the item's content area, not its branch."""

    def paint(self, painter, option, index):
        if option.state & QStyle.StateFlag.State_Selected:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            selection_color = QColor(styles.COLORS['primary'])
            selection_color.setAlpha(38)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(selection_color)
            painter.drawRoundedRect(option.rect.adjusted(0, 0, -1, 0), 12, 12)
            painter.restore()

        super().paint(painter, option, index)


class CategoryTree(QWidget):
    """
    Modern tree view widget showing categories and subcategories.
    
    Features:
    - Folder icons with amber color
    - Image counts per category
    - Collapsible tree structure
    - Selected subcategory highlighted in primary color
    
    Signals:
        selection_changed: Emitted when user selects a category/subcategory.
                          Args: (category_id, subcategory_id or None)
        data_changed: Emitted when categories are added/renamed/deleted.
    """
    
    selection_changed = pyqtSignal(str, object)  # category_id, subcategory_id (or None)
    data_changed = pyqtSignal()
    
    # Custom data roles for tree items
    ROLE_ID = Qt.ItemDataRole.UserRole
    ROLE_TYPE = Qt.ItemDataRole.UserRole + 1  # 'category' or 'subcategory'
    ROLE_PARENT_ID = Qt.ItemDataRole.UserRole + 2  # for subcategories
    ROLE_NAME = Qt.ItemDataRole.UserRole + 3  # store raw name
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._setup_ui()
        self._load_data()
        _i18n.get_manager().language_changed.connect(self._retranslate)

    def refresh_theme(self):
        self.setStyleSheet(styles.CATEGORY_TREE_STYLE)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Button bar for adding categories/subcategories
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self._add_cat_btn = QPushButton()
        self._add_cat_btn.setToolTip("Add a new category")
        self._add_cat_btn.setStyleSheet(styles.CATEGORY_ACTION_BUTTON_STYLE)
        self._add_cat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_cat_btn.clicked.connect(self._add_category)
        btn_layout.addWidget(self._add_cat_btn)
        
        self._add_subcat_btn = QPushButton()
        self._add_subcat_btn.setToolTip("Add a new subcategory")
        self._add_subcat_btn.setStyleSheet(styles.CATEGORY_ACTION_BUTTON_STYLE)
        self._add_subcat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_subcat_btn.clicked.connect(self._add_subcategory)
        btn_layout.addWidget(self._add_subcat_btn)
        
        layout.addLayout(btn_layout)
        
        # "Show All" button
        self._show_all_btn = QPushButton()
        self._show_all_btn.setIcon(ui_icon("image", "white"))
        self._show_all_btn.setIconSize(icon_size(18))
        self._show_all_btn.setStyleSheet(styles.SHOW_ALL_BUTTON_STYLE)
        self._show_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._show_all_btn.clicked.connect(self._show_all)
        layout.addWidget(self._show_all_btn)
        
        self._retranslate_buttons()
        
        # Tree container with rounded corners
        tree_container = QWidget()
        tree_container.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }}
        """)
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(8, 8, 8, 8)
        tree_layout.setSpacing(0)
        
        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setItemDelegate(CategoryTreeItemDelegate(self.tree))
        self.tree.setStyleSheet(styles.CATEGORY_TREE_STYLE + styles.SCROLLBAR_STYLE + f"""
            QTreeWidget {{
                font-family: {styles.FONTS['family']};
            }}
        """)
        self.tree.setIndentation(18)
        self.tree.setIconSize(icon_size(18))
        self.tree.setAnimated(True)
        self.tree.setRootIsDecorated(False)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemCollapsed.connect(self._on_item_collapsed)
        tree_layout.addWidget(self.tree)
        
        layout.addWidget(tree_container, 1)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
    
    def _load_data(self):
        """Load categories and subcategories from database."""
        self.tree.clear()
        
        # Get all categories
        categories = database.get_all_categories()
        
        for cat in categories:
            # Get image count for this category
            images = database.get_images_by_category(cat['id'], None)
            count = len(images)
            
            # Create category item with folder icon and count
            cat_item = QTreeWidgetItem()
            cat_item.setData(0, self.ROLE_ID, cat['id'])
            cat_item.setData(0, self.ROLE_TYPE, 'category')
            cat_item.setData(0, self.ROLE_NAME, cat['name'])
            
            # Use a bundled outline folder; open/closed state is represented
            # by the icon rather than an emoji or text glyph.
            cat_item.setText(0, cat['name'])
            cat_item.setIcon(0, ui_icon("folder-open", styles.COLORS['warning_icon'], 18))
            
            # Style: bold for categories
            font = cat_item.font(0)
            font.setWeight(500)
            cat_item.setFont(0, font)
            
            self.tree.addTopLevelItem(cat_item)
            
            # Get subcategories for this category
            subcategories = database.get_subcategories_for_category(cat['id'])
            
            if subcategories:
                # Check if there are images with no subcategory
                has_no_subcat_images = any(img.get('subcategory_id') is None for img in images)
                if has_no_subcat_images:
                    none_item = QTreeWidgetItem()
                    none_item.setText(0, "(none)")
                    none_item.setIcon(0, ui_icon("minus", styles.COLORS['text_light'], 16))
                    none_item.setData(0, self.ROLE_ID, "__none__")
                    none_item.setData(0, self.ROLE_TYPE, 'subcategory')
                    none_item.setData(0, self.ROLE_PARENT_ID, cat['id'])
                    none_item.setData(0, self.ROLE_NAME, "(none)")
                    none_item.setForeground(0, Qt.GlobalColor.darkGray)
                    cat_item.addChild(none_item)

            for subcat in subcategories:
                subcat_item = QTreeWidgetItem()
                subcat_item.setText(0, subcat['name'])
                subcat_item.setData(0, self.ROLE_ID, subcat['id'])
                subcat_item.setData(0, self.ROLE_TYPE, 'subcategory')
                subcat_item.setData(0, self.ROLE_PARENT_ID, cat['id'])
                subcat_item.setData(0, self.ROLE_NAME, subcat['name'])
                
                # Indent styling for subcategories
                subcat_item.setForeground(0, Qt.GlobalColor.darkGray)
                
                cat_item.addChild(subcat_item)
        
        # Expand all by default
        self.tree.expandAll()
    
    def refresh(self):
        """Refresh the tree from database."""
        self._load_data()

    def _retranslate_buttons(self):
        """Update button labels to current language."""
        self._add_cat_btn.setText(t("add_category_btn"))
        self._add_subcat_btn.setText(t("add_subcategory_btn"))
        self._show_all_btn.setText(t("show_all_btn"))

    def _retranslate(self):
        """Update all translatable UI strings."""
        self._retranslate_buttons()

    def refresh_theme(self):
        self.setStyleSheet(styles.CATEGORY_TREE_STYLE)
    
    def _add_category(self):
        """Show dialog to add a new category."""
        dialog = AddCategoryDialog(self)
        if dialog.exec():
            name = dialog.get_name()
            try:
                cat_id = uuid.uuid4().hex[:8]
                database.create_category(cat_id, name, datetime.now().isoformat())
                self.refresh()
                self.data_changed.emit()
            except Exception as e:
                show_error(self, t("error_title"), t("error_create_category", error=e))
    
    def _add_subcategory(self):
        """Show dialog to add a new subcategory."""
        categories = [(c['id'], c['name']) for c in database.get_all_categories()]
        
        if not categories:
            show_error(self, t("error_title"), t("error_no_categories"))
            return
        
        # Get currently selected category if any
        preselect = None
        selected = self.tree.currentItem()
        if selected:
            item_type = selected.data(0, self.ROLE_TYPE)
            if item_type == 'category':
                preselect = selected.data(0, self.ROLE_ID)
            elif item_type == 'subcategory':
                preselect = selected.data(0, self.ROLE_PARENT_ID)
        
        dialog = AddSubcategoryDialog(categories, self, preselect)
        if dialog.exec():
            name = dialog.get_name()
            category_id = dialog.get_category_id()
            try:
                subcat_id = uuid.uuid4().hex[:8]
                database.create_subcategory(subcat_id, name, category_id, datetime.now().isoformat())
                self.refresh()
                self.data_changed.emit()
            except Exception as e:
                show_error(self, t("error_title"), t("error_create_subcategory", error=e))
    
    def _show_context_menu(self, position):
        """Show right-click context menu for tree items."""
        item = self.tree.itemAt(position)
        if not item or item.data(0, self.ROLE_ID) == "__none__":
            return
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {styles.COLORS['card_light']};
                border: 1px solid {styles.COLORS['border']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {styles.COLORS['primary']};
                color: white;
            }}
        """)
        
        item_type = item.data(0, self.ROLE_TYPE)
        item_id = item.data(0, self.ROLE_ID)
        
        # Rename action
        rename_action = QAction(ui_icon("pencil", styles.COLORS['text_dark'], 18), t("rename_action"), self)
        rename_action.triggered.connect(lambda: self._rename_item(item))
        menu.addAction(rename_action)
        
        # Delete action
        delete_action = QAction(ui_icon("trash", styles.COLORS['danger'], 18), t("delete_action"), self)
        delete_action.triggered.connect(lambda: self._delete_item(item))
        menu.addAction(delete_action)
        
        menu.exec(self.tree.mapToGlobal(position))
    
    def _rename_item(self, item: QTreeWidgetItem):
        """Rename a category or subcategory."""
        item_type = item.data(0, self.ROLE_TYPE)
        item_id = item.data(0, self.ROLE_ID)
        
        current_name = item.data(0, self.ROLE_NAME)
        
        title = t("rename_category_title") if item_type == 'category' else t("rename_subcategory_title")
        dialog = RenameDialog(title, current_name, self)
        
        if dialog.exec():
            new_name = dialog.get_name()
            try:
                if item_type == 'category':
                    database.update_category(item_id, new_name)
                else:
                    database.update_subcategory(item_id, new_name)
                self.refresh()
                self.data_changed.emit()
            except Exception as e:
                show_error(self, t("error_title"), t("error_rename", error=e))
    
    def _delete_item(self, item: QTreeWidgetItem):
        """Delete a category or subcategory."""
        item_type = item.data(0, self.ROLE_TYPE)
        item_id = item.data(0, self.ROLE_ID)
        
        # Get name for confirmation from role
        name = item.data(0, self.ROLE_NAME)
        
        type_str = 'Category' if item_type == 'category' else 'Subcategory'
        
        if confirm_delete(self, type_str, name):
            try:
                if item_type == 'category':
                    database.delete_category(item_id)
                else:
                    database.delete_subcategory(item_id)
                self.refresh()
                self.data_changed.emit()
            except Exception as e:
                show_error(self, t("error_title"), t("error_delete", error=e))
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click - toggle expansion for categories."""
        from PyQt6.QtGui import QCursor
        item_type = item.data(0, self.ROLE_TYPE)
        if item_type == 'category':
            # Only toggle if click is near the left edge (on the arrow)
            pos = self.tree.viewport().mapFromGlobal(QCursor.pos())
            if pos.x() < 30:
                item.setExpanded(not item.isExpanded())
            
    def _on_item_expanded(self, item: QTreeWidgetItem):
        item_type = item.data(0, self.ROLE_TYPE)
        if item_type == 'category':
            item.setIcon(0, ui_icon("folder-open", styles.COLORS['warning_icon'], 18))

    def _on_item_collapsed(self, item: QTreeWidgetItem):
        item_type = item.data(0, self.ROLE_TYPE)
        if item_type == 'category':
            item.setIcon(0, ui_icon("folder", styles.COLORS['warning_icon'], 18))
            
    def _on_selection_changed(self):
        """Handle tree selection changes."""
        selected = self.tree.currentItem()
        if not selected:
            return
        
        item_type = selected.data(0, self.ROLE_TYPE)
        item_id = selected.data(0, self.ROLE_ID)
        
        # Update styling for selected item
        if item_type == 'subcategory':
            selected.setForeground(0, Qt.GlobalColor.magenta)
        
        if item_type == 'category':
            self.selection_changed.emit(item_id, None)
        else:  # subcategory
            parent_id = selected.data(0, self.ROLE_PARENT_ID)
            self.selection_changed.emit(parent_id, item_id)
    
    def _show_all(self):
        """Clear selection to show all images."""
        self.tree.clearSelection()
        self.selection_changed.emit("", None)  # Empty string signals "show all"
    
    def get_categories(self) -> List[tuple]:
        """Get list of (category_id, category_name) tuples."""
        return [(c['id'], c['name']) for c in database.get_all_categories()]
    
    def get_subcategories(self) -> List[tuple]:
        """Get list of (subcategory_id, name, category_id) tuples."""
        return [(s['id'], s['name'], s['category_id']) for s in database.get_all_subcategories()]

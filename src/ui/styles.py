"""
Shared styles for NikkiBook UI.
Defines the color palette and common style constants matching the reference design.
"""

# Color Palette (from reference UI)
COLORS = {
    # Primary accent color
    'primary': '#be5a8d',
    'primary_hover': '#a8507c',
    'primary_shadow': 'rgba(190, 90, 141, 0.3)',
    
    # Backgrounds
    'background_light': '#f3e8ee',
    'sidebar_light': '#e9d5df',
    'card_light': '#ffffff',
    'header_light': '#ffffff',
    
    # Dark mode (for future)
    'background_dark': '#1a1618',
    'sidebar_dark': '#2d2429',
    'card_dark': '#362c32',
    
    # Text
    'text_dark': '#1e293b',
    'text_medium': '#64748b',
    'text_light': '#94a3b8',
    
    # Utility
    'border': 'rgba(0, 0, 0, 0.05)',
    'hover_bg': 'rgba(0, 0, 0, 0.05)',
    'overlay': 'rgba(0, 0, 0, 0.6)',
    
    # Status
    'success': '#22c55e',
    'danger': '#ef4444',
    'danger_bg': 'rgba(239, 68, 68, 0.1)',
    'warning_icon': '#eab308',  # Amber for folder icons
}

# Font settings
FONTS = {
    'family': 'Inter, Roboto, "Segoe UI", "Noto Sans SC", "Noto Sans JP", "Microsoft YaHei", Meiryo, sans-serif',
    'size_xs': '10px',
    'size_sm': '11px',
    'size_base': '13px',
    'size_lg': '15px',
    'size_xl': '18px',
    'size_2xl': '24px',
}

def get_font_family(lang: str) -> str:
    """Return the optimized font family stack for the given language."""
    if lang == "zh":
        return '"Noto Sans SC", "Noto Sans JP", Inter, Roboto, "Segoe UI", "Microsoft YaHei", sans-serif'
    elif lang == "ja":
        return '"Noto Sans JP", "Noto Sans SC", Inter, Roboto, "Segoe UI", Meiryo, sans-serif'
    else:
        return 'Inter, Roboto, "Segoe UI", "Noto Sans SC", "Noto Sans JP", "Microsoft YaHei", Meiryo, sans-serif'

def get_global_stylesheet(lang: str) -> str:
    """Generate the global application stylesheet with language-optimized font stack."""
    family = get_font_family(lang)
    return f"* {{ font-family: {family}; }}\n" + """
        QMainWindow, QWidget {
            background-color: #DA9FBC;
            color: #2D2D2D;
        }
        QTreeWidget {
            background-color: #E9D6DE;
            border: 1px solid #BF588D;
            border-radius: 8px;
            outline: none;
        }
        QTreeWidget::item {
            padding: 8px;
            color: #2D2D2D;
        }
        QTreeWidget::item:selected {
            background-color: #BF588D;
            color: #ffffff;
        }
        QTreeWidget::item:hover {
            background-color: #DA9FBC;
        }
        QPushButton {
            background-color: #BF588D;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #D96BA3;
        }
        QPushButton:pressed {
            background-color: #A64B7A;
        }
        QLineEdit {
            background-color: #E9D6DE;
            border: 1px solid #BF588D;
            border-radius: 6px;
            padding: 8px;
            color: #2D2D2D;
        }
        QLineEdit:focus {
            border: 2px solid #BF588D;
        }
        QComboBox {
            background-color: #E9D6DE;
            border: 1px solid #BF588D;
            border-radius: 6px;
            padding: 8px;
            color: #2D2D2D;
        }
        QComboBox:hover {
            border: 1px solid #BF588D;
        }
        QComboBox::drop-down {
            border: none;
            padding-right: 8px;
        }
        QComboBox QAbstractItemView {
            background-color: #E9D6DE;
            selection-background-color: #BF588D;
            color: #2D2D2D;
        }
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        QScrollBar:vertical {
            background-color: #DA9FBC;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background-color: #939393;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #7A7A7A;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            background-color: #DA9FBC;
            height: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal {
            background-color: #939393;
            border-radius: 6px;
            min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #7A7A7A;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        QLabel {
            color: #2D2D2D;
        }
        QSplitter::handle {
            background-color: #BF588D;
        }
        QMessageBox {
            background-color: #DA9FBC;
        }
        QMessageBox QLabel {
            color: #2D2D2D;
        }
        QMessageBox QPushButton {
            min-width: 80px;
        }
        QDialog {
            background-color: #DA9FBC;
        }
        QMenu {
            background-color: #E9D6DE;
            border: 1px solid #BF588D;
            border-radius: 8px;
            padding: 4px;
            color: #2D2D2D;
        }
        QMenu::item {
            padding: 8px 24px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background-color: #BF588D;
            color: #ffffff;
        }
    """

# Spacing
SPACING = {
    'xs': '4px',
    'sm': '8px',
    'md': '12px',
    'lg': '16px',
    'xl': '24px',
    '2xl': '32px',
}

# Border radius
RADIUS = {
    'sm': '6px',
    'md': '8px',
    'lg': '12px',
    'xl': '16px',
    '2xl': '24px',
    'full': '9999px',
}

# Main window styles
MAIN_WINDOW_STYLE = f"""
    QMainWindow {{
        background-color: {COLORS['background_light']};
    }}
"""

# Header bar styles
HEADER_STYLE = f"""
    QWidget#header {{
        background-color: {COLORS['header_light']};
        border-bottom: 1px solid {COLORS['border']};
    }}
"""

# Search input styles
SEARCH_INPUT_STYLE = f"""
    QLineEdit {{
        background-color: #f1f5f9;
        border: none;
        border-radius: {RADIUS['xl']};
        padding: 10px 12px 10px 40px;
        font-size: {FONTS['size_base']};
        color: {COLORS['text_dark']};
    }}
    QLineEdit:focus {{
        background-color: {COLORS['card_light']};
        outline: none;
        border: 2px solid {COLORS['primary']};
    }}
    QLineEdit::placeholder {{
        color: {COLORS['text_light']};
    }}
"""

# Sort dropdown styles
SORT_COMBO_STYLE = f"""
    QComboBox {{
        background-color: #f1f5f9;
        border: none;
        border-radius: {RADIUS['lg']};
        padding: 8px 32px 8px 12px;
        font-size: {FONTS['size_sm']};
        color: {COLORS['text_dark']};
        min-width: 130px;
    }}
    QComboBox:hover {{
        background-color: #e2e8f0;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLORS['card_light']};
        border: 1px solid {COLORS['border']};
        border-radius: {RADIUS['lg']};
        selection-background-color: {COLORS['primary']};
        selection-color: white;
        padding: 4px;
    }}
"""

# Primary button styles
PRIMARY_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: {RADIUS['xl']};
        padding: 10px 20px;
        font-size: {FONTS['size_base']};
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {COLORS['primary_hover']};
    }}
    QPushButton:pressed {{
        background-color: #944470;
    }}
"""

# Icon button styles
ICON_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: #f1f5f9;
        border: none;
        border-radius: {RADIUS['xl']};
        padding: 10px;
        font-size: {FONTS['size_base']};
    }}
    QPushButton:hover {{
        background-color: #e2e8f0;
    }}
"""

# Sidebar styles
SIDEBAR_STYLE = f"""
    QWidget#sidebar {{
        background-color: {COLORS['sidebar_light']};
        border-right: 1px solid {COLORS['border']};
    }}
"""

# Category tree styles
CATEGORY_TREE_STYLE = f"""
    QTreeWidget {{
        background-color: transparent;
        border: none;
        outline: none;
        font-size: {FONTS['size_sm']};
        show-decoration-selected: 0;
    }}
    QTreeWidget::item {{
        padding: 8px 8px;
        border-radius: {RADIUS['lg']};
        margin: 2px 0;
    }}
    QTreeWidget::item:hover {{
        background-color: {COLORS['hover_bg']};
    }}
    QTreeWidget::item:selected {{
        background: transparent;
        color: {COLORS['primary']};
    }}
    QTreeWidget::branch {{
        background: transparent;
    }}
    QTreeWidget::branch:selected {{
        background: transparent;
    }}
"""

# Gallery card styles
CARD_STYLE = f"""
    QFrame#card {{
        background-color: {COLORS['card_light']};
        border-radius: {RADIUS['2xl']};
        border: none;
    }}
    QFrame#card:hover {{
        border: 2px solid {COLORS['primary']};
    }}
"""

# Thumbnail widget styles  
THUMBNAIL_STYLE = f"""
    ThumbnailWidget {{
        background-color: {COLORS['card_light']};
        border-radius: {RADIUS['2xl']};
        border: none;
    }}
    ThumbnailWidget:hover {{
        border: none;
    }}
"""

# Share input styles
SHARE_INPUT_STYLE = f"""
    QLineEdit {{
        background-color: transparent;
        border: none;
        padding: 4px 0;
        font-size: {FONTS['size_xs']};
        font-weight: 500;
        color: {COLORS['text_medium']};
    }}
    QLineEdit:focus {{
        border: none;
        outline: none;
    }}
"""

# Copy button styles
COPY_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: #f1f5f9;
        border: none;
        border-radius: {RADIUS['lg']};
        padding: 6px;
        color: {COLORS['primary']};
    }}
    QPushButton:hover {{
        background-color: {COLORS['primary']};
        color: white;
    }}
"""

# Modal styles
MODAL_OVERLAY_COLOR = COLORS['overlay']

MODAL_CONTENT_STYLE = f"""
    QWidget#modalContent {{
        background-color: {COLORS['background_light']};
        border-radius: {RADIUS['2xl']};
    }}
"""

MODAL_CLOSE_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: rgba(255, 255, 255, 0.1);
        border: none;
        border-radius: 20px;
        color: white;
        font-size: 18px;
    }}
    QPushButton:hover {{
        background-color: rgba(255, 255, 255, 0.2);
    }}
"""

# Form field styles
FORM_LABEL_STYLE = f"""
    QLabel {{
        font-size: {FONTS['size_xs']};
        font-weight: 700;
        color: {COLORS['text_light']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        background-color: transparent;
        border: none;
    }}
"""

FORM_INPUT_STYLE = f"""
    QLineEdit, QComboBox {{
        background-color: #e2e8f0;
        border: none;
        border-radius: {RADIUS['xl']};
        padding: 12px 16px;
        font-size: {FONTS['size_sm']};
        color: {COLORS['text_dark']};
    }}
    QLineEdit:focus, QComboBox:focus {{
        background-color: {COLORS['card_light']};
        border: 2px solid {COLORS['primary']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
"""

FORM_INPUT_DISABLED_STYLE = f"""
    QLineEdit {{
        background-color: #e2e8f0;
        border: none;
        border-radius: {RADIUS['xl']};
        padding: 12px 16px;
        font-size: {FONTS['size_sm']};
        color: {COLORS['text_light']};
    }}
"""

# Save button styles
SAVE_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: {RADIUS['2xl']};
        padding: 16px;
        font-size: {FONTS['size_base']};
        font-weight: 700;
    }}
    QPushButton:hover {{
        background-color: {COLORS['primary_hover']};
    }}
"""

# Delete button styles
DELETE_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['danger_bg']};
        color: {COLORS['danger']};
        border: none;
        border-radius: {RADIUS['2xl']};
        padding: 16px;
        font-size: {FONTS['size_base']};
        font-weight: 700;
    }}
    QPushButton:hover {{
        background-color: {COLORS['danger']};
        color: white;
    }}
"""

# Show All button styles
SHOW_ALL_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: #4a4e69;
        color: white;
        border: none;
        border-radius: {RADIUS['lg']};
        padding: 12px 16px;
        font-size: {FONTS['size_sm']};
        font-weight: 500;
        text-align: left;
    }}
    QPushButton:hover {{
        background-color: #5a5e79;
    }}
"""

# Category action buttons
CATEGORY_ACTION_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: rgba(190, 90, 141, 0.15);
        color: {COLORS['primary']};
        border: 1px solid rgba(190, 90, 141, 0.3);
        border-radius: {RADIUS['lg']};
        padding: 8px 12px;
        font-size: {FONTS['size_xs']};
        font-weight: 700;
        text-transform: uppercase;
    }}
    QPushButton:hover {{
        background-color: rgba(190, 90, 141, 0.25);
    }}
"""

# Scrollbar styles
SCROLLBAR_STYLE = """
    QScrollBar:vertical {
        background: transparent;
        width: 6px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background: rgba(190, 90, 141, 0.3);
        min-height: 30px;
        border-radius: 3px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(190, 90, 141, 0.5);
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: transparent;
    }
"""

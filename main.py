"""
NikkiBook - Image Catalog Application
Entry point for the application.
"""
import sys
import os
from src.config import ensure_directories
from src.database import init_database
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from src.ui.main_window import MainWindow
from src.ui.styles import FONTS

# Suppress libpng warnings about incorrect sRGB profiles
os.environ["QT_LOGGING_RULES"] = "qt.gui.icc=false"


def main():
    """Initialize and run the NikkiBook application."""
    # Ensure all required directories exist
    ensure_directories()
    
    # Initialize database (creates tables on first run)
    init_database()
    
    # Create Qt application
    # Enable high DPI scaling for modern displays
    app = QApplication(sys.argv)
    app.setApplicationName("NikkiBook")
    app.setOrganizationName("NikkiBook")
    
    # Set default application font to prevent font size issues
    # Use the robust font fallback stack targeting CJK texts
    font = QFont()
    families = [f.strip(' "\'') for f in FONTS['family'].split(',')]
    font.setFamilies(families)
    font.setPointSize(10)
    app.setFont(font)
    
    # Apply custom pink theme stylesheet (Slightly darkened for comfort)
    app.setStyleSheet(f"* {{ font-family: {FONTS['family']}; }}\n" + """
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
    """)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

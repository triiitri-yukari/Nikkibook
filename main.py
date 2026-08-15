"""
NikkiBook - Image Catalog Application
Entry point for the application.
"""
import sys
import os
import ctypes
from src.config import ensure_directories, APP_ICON_PATH
from src.database import init_database
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from src.ui.main_window import MainWindow
from src.ui import styles
from src.ui.fonts import load_application_fonts
import src.i18n as _i18n

# Suppress libpng warnings about incorrect sRGB profiles
os.environ["QT_LOGGING_RULES"] = "qt.gui.icc=false"


def _set_windows_app_user_model_id():
    """Give Windows a stable taskbar identity for the NikkiBook window."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "NikkiBook.NikkiBook"
            )
        except (AttributeError, OSError):
            pass


def main():
    """Initialize and run the NikkiBook application."""
    # Ensure all required directories exist
    ensure_directories()
    
    # Initialize database (creates tables on first run)
    init_database()
    
    _set_windows_app_user_model_id()

    # Create Qt application
    # Enable high DPI scaling for modern displays
    app = QApplication(sys.argv)
    app.setApplicationName("NikkiBook")
    app.setOrganizationName("NikkiBook")

    app_icon = QIcon(str(APP_ICON_PATH))
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    
    # Load fonts from local resources/fonts folder (requires QApplication initialized)
    load_application_fonts()
    
    # Set default application font to prevent font size issues
    # Use the robust font fallback stack targeting CJK texts
    font = QFont()
    families = [f.strip(' "\'') for f in styles.FONTS['family'].split(',')]
    font.setFamilies(families)
    font.setPointSize(10)
    app.setFont(font)
    
    # Apply custom pink theme stylesheet (Slightly darkened for comfort)
    lang = _i18n.get_manager().language
    app.setStyleSheet(styles.get_global_stylesheet(lang))
    
    # Create and show main window
    window = MainWindow()
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

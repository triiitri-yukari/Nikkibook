"""
Font loading utility for NikkiBook.
"""
import sys
from pathlib import Path
from PyQt6.QtGui import QFontDatabase
from ..config import APP_DIR

# In a one-file build, PyInstaller extracts embedded data under _MEIPASS.
# Source runs retain the existing src/resources/fonts location.
if getattr(sys, "frozen", False):
    FONTS_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR)) / "resources" / "fonts"
else:
    FONTS_DIR = APP_DIR / "src" / "resources" / "fonts"

def load_application_fonts():
    """
    Scan the resources/fonts directory and load all found .ttf and .otf files
    into the application's font database.
    """
    if not FONTS_DIR.exists():
        print(f"Font directory not found: {FONTS_DIR}")
        return
        
    loaded_count = 0
    for font_file in FONTS_DIR.iterdir():
        if font_file.suffix.lower() in ('.ttf', '.otf'):
            # Load font file into QFontDatabase
            font_id = QFontDatabase.addApplicationFont(str(font_file.absolute()))
            
            if font_id == -1:
                print(f"Warning: Failed to load font file: {font_file.name}")
            else:
                families = QFontDatabase.applicationFontFamilies(font_id)
                loaded_count += 1
                # Optional: log loaded families for debugging
                # print(f"Successfully loaded font: {font_file.name} ({', '.join(families)})")
                
    if loaded_count > 0:
        print(f"Loaded {loaded_count} application font(s) from local resources.")

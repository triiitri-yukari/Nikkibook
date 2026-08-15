# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the portable NikkiBook production folder."""

import sys
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH)

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # CJK and logo fonts are required at runtime and are bundled in the
        # private runtime folder. User-editable snap templates stay external.
        (str(project_root / 'src' / 'resources' / 'fonts'), 'resources/fonts'),
        # The same ICO used by the EXE is needed by Qt for the window/taskbar.
        (str(project_root / 'assets' / 'icon.ico'), 'resources'),
    ],
    hiddenimports=[
        # PyQt6 hidden imports (sometimes needed)
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        'PyQt6.sip',
        # Imports used dynamically by the Snap workflow.
        'win32con',
        'win32gui',
        'win32clipboard',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unused PyQt6 modules to reduce size
        'PyQt6.QtNetwork',
        'PyQt6.QtOpenGL',
        'PyQt6.QtQml',
        'PyQt6.QtQuick',
        'PyQt6.QtSql',
        'PyQt6.QtTest',
        'PyQt6.QtXml',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NikkiBook',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Use UPX compression if available
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'assets' / 'icon.ico'),
    # Request elevation by default for portable data writes and Snap control.
    uac_admin=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NikkiBook',
)

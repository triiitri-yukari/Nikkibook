"""Reusable plain-outline icons for the NikkiBook interface.

The application is distributed as a self-contained Windows build, so the
icons are rendered from small local SVG paths instead of depending on a
platform icon font or an installed theme. Every icon uses the same 1.8px
rounded stroke for a consistent, outline-only visual language.
"""

from functools import lru_cache

from PyQt6.QtCore import QByteArray, QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer


_ICON_PATHS = {
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4 4"/>',
    "image": (
        '<rect x="3" y="4" width="18" height="16" rx="2"/>'
        '<circle cx="8.5" cy="9" r="1.5"/>'
        '<path d="m3 16 5-5 4 4 3-3 6 6"/>'
    ),
    "image-plus": (
        '<rect x="3" y="4" width="14" height="15" rx="2"/>'
        '<circle cx="8" cy="9" r="1.5"/>'
        '<path d="m3 15 4-4 3 3 2-2 5 5"/>'
        '<path d="M19 14v6M16 17h6"/>'
    ),
    "camera": (
        '<path d="M4 7h3l1.5-2h7L17 7h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z"/>'
        '<circle cx="12" cy="13" r="3.5"/>'
    ),
    "settings": (
        '<circle cx="12" cy="12" r="3.25"/>'
        '<path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M18.7 5.3l-2.1 2.1M7.4 16.6l-2.1 2.1"/>'
    ),
    "folder": (
        '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>'
    ),
    "folder-open": (
        '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2"/>'
        '<path d="M3 9h18l-2 10H5L3 9Z"/>'
    ),
    "folder-plus": (
        '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>'
        '<path d="M17 11v6M14 14h6"/>'
    ),
    "tag": (
        '<path d="M4 5h6l9 9a2 2 0 0 1 0 2.8l-2.2 2.2a2 2 0 0 1-2.8 0L5 10V5Z"/>'
        '<circle cx="8.5" cy="8.5" r="1"/>'
    ),
    "list-plus": '<path d="M5 6h9M5 12h9M5 18h7"/><path d="M18 14v6M15 17h6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "file-image": (
        '<path d="M6 3h8l4 4v14H6Z"/>'
        '<path d="M14 3v5h5"/>'
        '<circle cx="10" cy="12" r="1.2"/>'
        '<path d="m8 18 3-3 2 2 1.5-1.5L18 19"/>'
    ),
    "copy": (
        '<rect x="7" y="7" width="12" height="12" rx="2"/>'
        '<path d="M17 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h2"/>'
    ),
    "check": '<path d="m5 12 4 4L19 6"/>',
    "trash": (
        '<path d="M4 7h16M10 11v6M14 11v6M9 7V4h6v3"/>'
        '<path d="m6 7 1 14h10l1-14"/>'
    ),
    "pencil": '<path d="m4 16-.7 4.7L8 20l11.5-11.5a2.1 2.1 0 0 0-3-3Z"/><path d="m14.5 6.5 3 3"/>',
    "x": '<path d="m6 6 12 12M18 6 6 18"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "chevron-right": '<path d="m9 6 6 6-6 6"/>',
}


def _stroke_color(color: str) -> str:
    qcolor = QColor(color)
    return qcolor.name(QColor.NameFormat.HexRgb) if qcolor.isValid() else "#64748b"


@lru_cache(maxsize=128)
def _icon_pixmap(name: str, color: str, size: int) -> QPixmap:
    try:
        path_data = _ICON_PATHS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown NikkiBook icon: {name}") from exc

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24">
        <g fill="none" stroke="{_stroke_color(color)}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            {path_data}
        </g>
    </svg>'''.encode("utf-8")

    renderer = QSvgRenderer(QByteArray(svg))
    if not renderer.isValid():
        raise ValueError(f"Could not render NikkiBook icon: {name}")

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    return pixmap


def icon(name: str, color: str = "#64748b", size: int = 20) -> QIcon:
    """Return a cached outline icon rendered at ``size`` pixels."""
    return QIcon(_icon_pixmap(name, color, size))


def pixmap(name: str, color: str = "#64748b", size: int = 20) -> QPixmap:
    """Return a pixmap for icon-only labels and empty states."""
    return _icon_pixmap(name, color, size)


def icon_size(size: int) -> QSize:
    """Return a QSize helper for consistent icon sizing in widgets."""
    return QSize(size, size)

"""Inline SVG icons rendered into ``QIcon`` at the requested color and size.

These are small Lucide-style outlined glyphs used in the toolbar buttons.
Keeping the SVG strings inline avoids dragging extra files around and lets
us tint the icon per button (white on the primary buttons, blue on the
secondary ones).
"""

from __future__ import annotations

from PyQt6.QtCore import QByteArray, QSize, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer


# fmt: off
_SVG: dict[str, str] = {
    "folder": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/></svg>""",
    "save":   """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>""",
    "show":   """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>""",
    "blur_all":  """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3l18 18"/><path d="M10.58 10.59A2 2 0 0 0 12 14a2 2 0 0 0 1.41-.59"/><path d="M9.88 5.09A10.7 10.7 0 0 1 12 5c5 0 9.27 3.11 11 7-.62 1.39-1.5 2.6-2.6 3.61"/><path d="M6.61 6.61A10.95 10.95 0 0 0 1 12c1.73 3.89 6 7 11 7 1.85 0 3.6-.42 5.12-1.16"/></svg>""",
    "blur_none": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>""",
    "refresh":   """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 4 21 10 15 10"/><polyline points="3 20 3 14 9 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L21 8"/><path d="M20.49 15a9 9 0 0 1-14.85 3.36L3 16"/></svg>""",
    "dot":       """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="6" fill="currentColor"/></svg>""",
}
# fmt: on


def icon(name: str, color: str = "#ffffff", size: int = 16) -> QIcon:
    """Return a ``QIcon`` for ``name`` tinted in ``color`` at ``size`` px."""
    if name not in _SVG:
        raise KeyError(name)
    svg_str = _SVG[name].replace("currentColor", color)
    data = QByteArray(svg_str.encode("utf-8"))
    renderer = QSvgRenderer(data)
    pix = QPixmap(QSize(size, size))
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)

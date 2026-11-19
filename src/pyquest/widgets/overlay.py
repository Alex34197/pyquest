"""
overlay.py — superposición sutil de "scanlines" CRT (desactivable).
overlay.py — subtle CRT scanline overlay (toggleable).

Pinta líneas horizontales semitransparentes por encima del contenido. Es
deliberadamente discreto ("no exagerado"): se puede desactivar en el menú Ver.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class ScanlineOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._enabled = True

    def set_enabled(self, on: bool) -> None:
        self._enabled = on
        self.setVisible(on)
        self.update()

    def paintEvent(self, event):
        if not self._enabled:
            return
        painter = QPainter(self)
        line = QColor(0, 0, 0, 34)        # negro muy translúcido
        y = 0
        w = self.width()
        h = self.height()
        while y < h:
            painter.fillRect(0, y, w, 1, line)
            y += 3

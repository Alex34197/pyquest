"""
history_input.py — campo de entrada con historial (flechas ↑/↓).
history_input.py — input field with command history (Up/Down arrows).

Como una terminal: guarda lo que escribes y lo recuperas con las flechas.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit


class HistoryInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._history: list[str] = []
        self._idx = 0

    def remember(self, text: str) -> None:
        """Guarda una entrada en el historial (evita duplicados consecutivos)."""
        text = text.strip()
        if text and (not self._history or self._history[-1] != text):
            self._history.append(text)
        self._idx = len(self._history)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up and self._history:
            self._idx = max(0, self._idx - 1)
            self.setText(self._history[self._idx])
            return
        if event.key() == Qt.Key_Down and self._history:
            self._idx = min(len(self._history), self._idx + 1)
            self.setText(self._history[self._idx] if self._idx < len(self._history) else "")
            return
        super().keyPressEvent(event)

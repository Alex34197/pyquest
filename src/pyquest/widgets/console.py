"""
console.py — consola de salida estilo terminal (solo lectura, con colores).
console.py — terminal-style output console (read-only, colored).
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

from .. import theme

# Un print() dentro de un bucle infinito puede generar cientos de MB: la consola
# conserva solo las últimas MAX_LINES líneas y recorta cada bloque a MAX_CHARS.
MAX_LINES = 5000
MAX_CHARS = 200_000
TRUNCATED_NOTE = "\n[… salida recortada / output truncated …]\n"


class ConsoleOutput(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(theme.get_mono_font())
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.setMaximumBlockCount(MAX_LINES)

    def _append(self, text: str, color: str) -> None:
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + TRUNCATED_NOTE
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    @staticmethod
    def _nl(text: str) -> str:
        return text if text.endswith("\n") else text + "\n"

    def write_stdout(self, text: str) -> None:
        self._append(text, theme.FG)

    def write_error(self, text: str) -> None:
        self._append(self._nl(text), theme.ERROR)

    def write_ok(self, text: str) -> None:
        self._append(self._nl(text), theme.OK)

    def write_warn(self, text: str) -> None:
        self._append(self._nl(text), theme.WARN)

    def write_info(self, text: str) -> None:
        self._append(self._nl(text), theme.INFO)

    def write_dim(self, text: str) -> None:
        self._append(self._nl(text), theme.FG_DIM)

    # --- streaming (sin forzar salto de línea), para la consola interactiva --- #
    def stream_out(self, text: str) -> None:
        self._append(text, theme.FG)

    def stream_err(self, text: str) -> None:
        self._append(text, theme.ERROR)

    def clear_console(self) -> None:
        self.clear()

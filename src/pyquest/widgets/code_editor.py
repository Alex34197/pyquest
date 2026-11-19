"""
code_editor.py — editor de código con números de línea, resaltado de sintaxis
de Python, auto-indentado y tabulador = 4 espacios.
"""
from __future__ import annotations

import re

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import (
    QColor, QFont, QPainter, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QTextFormat,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from .. import theme


# --------------------------------------------------------------------------- #
# Resaltador de sintaxis
# --------------------------------------------------------------------------- #
def _fmt(color: str, bold=False, italic=False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Bold)
    if italic:
        f.setFontItalic(True)
    return f


class PythonHighlighter(QSyntaxHighlighter):
    KEYWORDS = [
        "and", "as", "assert", "async", "await", "break", "class", "continue",
        "def", "del", "elif", "else", "except", "finally", "for", "from",
        "global", "if", "import", "in", "is", "lambda", "nonlocal", "not", "or",
        "pass", "raise", "return", "try", "while", "with", "yield",
        "True", "False", "None",
    ]
    BUILTINS = [
        "print", "len", "range", "int", "str", "float", "list", "dict", "set",
        "tuple", "input", "sum", "min", "max", "abs", "sorted", "reversed",
        "enumerate", "zip", "map", "filter", "type", "bool", "open", "round",
        "isinstance", "format", "all", "any", "ord", "chr", "repr",
    ]

    def __init__(self, document):
        super().__init__(document)
        self.rules: list[tuple[re.Pattern, QTextCharFormat, int]] = []

        kw_fmt = _fmt(theme.SYN_KW, bold=True)
        for w in self.KEYWORDS:
            self.rules.append((re.compile(rf"\b{w}\b"), kw_fmt, 0))

        bi_fmt = _fmt(theme.SYN_BUILTIN)
        for w in self.BUILTINS:
            self.rules.append((re.compile(rf"\b{w}\b"), bi_fmt, 0))

        # nombre de función tras 'def' (coloreamos el grupo 1)
        self.rules.append((re.compile(r"\bdef\s+(\w+)"), _fmt(theme.SYN_FUNC, bold=True), 1))
        self.rules.append((re.compile(r"\bclass\s+(\w+)"), _fmt(theme.SYN_FUNC, bold=True), 1))

        # números
        self.rules.append((re.compile(r"\b[0-9]+\.?[0-9]*\b"), _fmt(theme.SYN_NUM), 0))

        # cadenas de una línea (se aplican antes que los comentarios)
        self.str_fmt = _fmt(theme.SYN_STR)
        self.rules.append((re.compile(r"'[^'\\\n]*(\\.[^'\\\n]*)*'"), self.str_fmt, 0))
        self.rules.append((re.compile(r'"[^"\\\n]*(\\.[^"\\\n]*)*"'), self.str_fmt, 0))

        # comentarios (al final, ganan a lo anterior)
        self.comment_fmt = _fmt(theme.SYN_COMMENT, italic=True)
        self.rules.append((re.compile(r"#[^\n]*"), self.comment_fmt, 0))

        # cadenas triples (multilínea)
        self.tri_single = re.compile(r"'''")
        self.tri_double = re.compile(r'"""')

    def highlightBlock(self, text: str) -> None:
        for rx, fmt, group in self.rules:
            for m in rx.finditer(text):
                start, end = m.start(group), m.end(group)
                self.setFormat(start, end - start, fmt)
        # multilínea (docstrings)
        self.setCurrentBlockState(0)
        if not self._match_multiline(text, self.tri_double, 1):
            self._match_multiline(text, self.tri_single, 2)

    def _match_multiline(self, text: str, delim: re.Pattern, state: int) -> bool:
        """Resalta cadenas triples que abarcan varias líneas (docstrings)."""
        DLEN = 3
        if self.previousBlockState() == state:
            start, add = 0, 0
        else:
            m = delim.search(text)
            start, add = (m.start(), DLEN) if m else (-1, 0)
        while start >= 0:
            m = delim.search(text, start + add)
            if m:  # se cierra en esta misma línea
                length = m.start() - start + DLEN
                self.setCurrentBlockState(0)
            else:  # no se cierra: el bloque queda "dentro" de la cadena
                self.setCurrentBlockState(state)
                length = len(text) - start
            self.setFormat(start, length, self.str_fmt)
            nxt = delim.search(text, start + length)
            start, add = (nxt.start(), DLEN) if nxt else (-1, 0)
        return self.currentBlockState() == state


# --------------------------------------------------------------------------- #
# Franja de números de línea
# --------------------------------------------------------------------------- #
class _LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.paint_line_numbers(event)


# --------------------------------------------------------------------------- #
# Editor
# --------------------------------------------------------------------------- #
class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._gutter = _LineNumberArea(self)

        self.setFont(theme.get_mono_font())
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))

        self._error_line = None

        self.blockCountChanged.connect(lambda _=0: self._update_margin())
        self.updateRequest.connect(self._on_update_request)
        self.cursorPositionChanged.connect(self._refresh_extra_selections)
        self.textChanged.connect(self.clear_error_line)

        self.highlighter = PythonHighlighter(self.document())
        self._update_margin()
        self._refresh_extra_selections()

    # --- números de línea --------------------------------------------------- #
    def line_number_area_width(self) -> int:
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 14 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_margin(self):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _on_update_request(self, rect, dy):
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(0, rect.y(), self._gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_margin()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._gutter.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def paint_line_numbers(self, event):
        painter = QPainter(self._gutter)
        painter.fillRect(event.rect(), QColor(theme.GUTTER_BG))
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        painter.setPen(QColor(theme.GUTTER_FG))
        height = self.fontMetrics().height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(
                    0, int(top), self._gutter.width() - 6, height,
                    Qt.AlignRight, str(number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            number += 1

    # --- resaltado de la línea actual -------------------------------------- #
    def set_error_line(self, line):
        """Resalta en rojo la línea (1-based) del error; None la quita."""
        self._error_line = line if (line and line >= 1) else None
        self._refresh_extra_selections()

    def clear_error_line(self):
        if self._error_line is not None:
            self._error_line = None
            self._refresh_extra_selections()

    def _refresh_extra_selections(self):
        selections = []
        # línea actual
        cur = QTextEdit.ExtraSelection()
        cur.format.setBackground(QColor(theme.CURRENT_LINE))
        cur.format.setProperty(QTextFormat.FullWidthSelection, True)
        c = self.textCursor()
        c.clearSelection()
        cur.cursor = c
        selections.append(cur)
        # línea con error (si la hay)
        if self._error_line:
            block = self.document().findBlockByNumber(self._error_line - 1)
            if block.isValid():
                err = QTextEdit.ExtraSelection()
                err.format.setBackground(QColor(theme.ERROR_LINE_BG))
                err.format.setProperty(QTextFormat.FullWidthSelection, True)
                ec = QTextCursor(block)
                ec.clearSelection()
                err.cursor = ec
                selections.append(err)
        self.setExtraSelections(selections)

    # --- comodidades de edición -------------------------------------------- #
    def rebuild_highlighter(self) -> None:
        """Recrea el resaltador con los colores del tema activo."""
        self.highlighter.setDocument(None)
        self.highlighter = PythonHighlighter(self.document())
        self.viewport().update()
        self._gutter.update()
        self._refresh_extra_selections()

    def set_font_size(self, pt: int) -> None:
        self.setFont(theme.get_mono_font(pt))
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))
        self._update_margin()
        self.viewport().update()
        self._gutter.update()

    def _selected_blocks(self):
        doc = self.document()
        cur = self.textCursor()
        first = doc.findBlock(cur.selectionStart())
        last = doc.findBlock(cur.selectionEnd())
        blocks, b = [], first
        while b.isValid():
            blocks.append(b)
            if b.blockNumber() == last.blockNumber():
                break
            b = b.next()
        return blocks

    def toggle_comment(self):
        """Comenta o descomenta las líneas seleccionadas (Ctrl+/)."""
        blocks = self._selected_blocks()
        nonempty = [b for b in blocks if b.text().strip()]
        if not nonempty:
            return
        all_commented = all(b.text().lstrip().startswith("#") for b in nonempty)
        cur = self.textCursor()
        cur.beginEditBlock()
        for b in blocks:
            text = b.text()
            if not text.strip():
                continue
            indent = len(text) - len(text.lstrip(" "))
            if all_commented:
                rest = text[indent:]
                rest = rest[2:] if rest.startswith("# ") else rest[1:]
                new = text[:indent] + rest
            else:
                new = text[:indent] + "# " + text[indent:]
            c = QTextCursor(b)
            c.select(QTextCursor.LineUnderCursor)
            c.insertText(new)
        cur.endEditBlock()

    def _shift_lines(self, dedent: bool):
        """Indenta (Tab) o desindenta (Mayús+Tab) las líneas seleccionadas."""
        blocks = self._selected_blocks()
        cur = self.textCursor()
        cur.beginEditBlock()
        for b in blocks:
            text = b.text()
            c = QTextCursor(b)
            if dedent:
                if text.startswith("    "):
                    new = text[4:]
                elif text[:1] in (" ", "\t"):
                    n = len(text) - len(text.lstrip(" \t"))
                    new = text[min(4, n):]
                else:
                    continue
                c.select(QTextCursor.LineUnderCursor)
                c.insertText(new)
            else:
                c.movePosition(QTextCursor.StartOfBlock)
                c.insertText("    ")
        cur.endEditBlock()

    def keyPressEvent(self, event):
        mods = event.modifiers()
        if event.key() == Qt.Key_Slash and (mods & Qt.ControlModifier):
            self.toggle_comment()
            return
        cur = self.textCursor()
        multi = (cur.hasSelection() and
                 self.document().findBlock(cur.selectionStart()).blockNumber()
                 != self.document().findBlock(cur.selectionEnd()).blockNumber())
        if event.key() == Qt.Key_Backtab or (event.key() == Qt.Key_Tab and (mods & Qt.ShiftModifier)):
            self._shift_lines(dedent=True)
            return
        if event.key() == Qt.Key_Tab:
            if multi:
                self._shift_lines(dedent=False)
                return
            self.insertPlainText("    ")
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            line = self.textCursor().block().text()
            indent = len(line) - len(line.lstrip(" "))
            extra = 4 if line.rstrip().endswith(":") else 0
            super().keyPressEvent(event)
            self.insertPlainText(" " * (indent + extra))
            return
        super().keyPressEvent(event)

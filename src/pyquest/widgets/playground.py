"""
playground.py — zona libre (REPL/playground): escribe y ejecuta Python.
playground.py — free coding area (REPL/playground): write and run Python.

No hay ejercicio ni tests: solo un editor, una consola y ejecución interactiva
(con input() en vivo), reutilizando la misma InteractiveSession del resto de la app.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QSplitter, QVBoxLayout,
)

from .code_editor import CodeEditor
from .console import ConsoleOutput
from .history_input import HistoryInput
from .interactive import InteractiveSession

_STARTER = {
    "es": [
        "# Playground: escribe Python libremente y pulsa Ejecutar (Ctrl+R).",
        "# input() funciona: usa la caja de abajo y pulsa Enter.",
        "",
        'print("¡Hola desde PyQuest!")',
        "",
        'nombre = input("¿Cómo te llamas? ")',
        'print("Encantado,", nombre)',
    ],
    "en": [
        "# Playground: write Python freely and press Run (Ctrl+R).",
        "# input() works: use the box below and press Enter.",
        "",
        'print("Hello from PyQuest!")',
        "",
        'nombre = input("What is your name? ")',
        'print("Nice to meet you,", nombre)',
    ],
}


class PlaygroundWindow(QDialog):
    """Ventana independiente (no modal) para experimentar con código."""

    def __init__(self, i18n, font_pt: int = 11, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setWindowTitle(i18n.t("playground_title"))
        self.setModal(False)
        self.resize(760, 600)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Vertical)
        self.editor = CodeEditor()
        self.console = ConsoleOutput()
        splitter.addWidget(self.editor)
        splitter.addWidget(self.console)
        splitter.setSizes([360, 200])
        root.addWidget(splitter, 1)

        in_row = QHBoxLayout()
        in_row.addWidget(QLabel(">"))
        self.input_line = HistoryInput()
        self.input_line.setObjectName("input_line")
        self.input_line.setPlaceholderText(i18n.t("input_placeholder"))
        self.input_line.setEnabled(False)
        self.input_line.returnPressed.connect(self._send_input)
        in_row.addWidget(self.input_line, 1)
        root.addLayout(in_row)

        buttons = QHBoxLayout()
        self.btn_run = QPushButton(i18n.t("btn_run"))
        self.btn_run.setObjectName("primary")
        self.btn_clear = QPushButton(i18n.t("btn_clear"))
        self.btn_run.clicked.connect(self.on_run)
        self.btn_clear.clicked.connect(self.on_clear)
        buttons.addWidget(self.btn_run)
        buttons.addWidget(self.btn_clear)
        buttons.addStretch(1)
        root.addLayout(buttons)

        self.session = InteractiveSession(self)
        self.session.output.connect(self.console.stream_out)
        self.session.errored.connect(self.console.stream_err)
        self.session.done.connect(self._on_finished)

        self.set_content_font_size(font_pt)
        self.editor.setPlainText("\n".join(_STARTER.get(i18n.lang, _STARTER["es"])))

        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.on_run)
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.on_run)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self.on_run)

    # ------------------------------------------------------------------ #
    def set_content_font_size(self, pt: int) -> None:
        if hasattr(self.editor, "set_font_size"):
            self.editor.set_font_size(pt)
        if hasattr(self.console, "set_font_size"):
            self.console.set_font_size(pt)

    def on_run(self) -> None:
        if self.session.is_running():
            self.session.stop()
            return
        self.console.clear_console()
        self.editor.clear_error_line()
        self.session.start(self.editor.toPlainText())
        self._set_running(True)
        self.input_line.setEnabled(True)
        self.input_line.setFocus()

    def _send_input(self) -> None:
        if self.session.is_running():
            text = self.input_line.text()
            self.session.send(text)
            self.console.stream_out(text + "\n")
            self.input_line.remember(text)
            self.input_line.clear()

    def _on_finished(self, code: int) -> None:
        self.input_line.setEnabled(False)
        self.input_line.clear()
        self._set_running(False)
        if code != 0 and self.session.err_buffer:
            from .. import runner
            exc = runner.parse_exception(self.session.err_buffer)
            if exc and exc.line:
                self.editor.set_error_line(exc.line)
        self.console.write_dim(f"[{self.i18n.t('process_ended')} · {code}]")

    def _set_running(self, running: bool) -> None:
        self.btn_run.setText(self.i18n.t("btn_stop") if running else self.i18n.t("btn_run"))

    def on_clear(self) -> None:
        self.console.clear_console()

    # ------------------------------------------------------------------ #
    def retranslate(self) -> None:
        self.setWindowTitle(self.i18n.t("playground_title"))
        self.input_line.setPlaceholderText(self.i18n.t("input_placeholder"))
        self.btn_clear.setText(self.i18n.t("btn_clear"))
        if not self.session.is_running():
            self.btn_run.setText(self.i18n.t("btn_run"))

    def refresh_theme(self) -> None:
        if hasattr(self.editor, "rebuild_highlighter"):
            self.editor.rebuild_highlighter()

    def closeEvent(self, event):
        self.session.stop()
        super().closeEvent(event)

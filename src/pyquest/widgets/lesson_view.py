"""
lesson_view.py — pestañas Teoría / Práctica para la lección activa.
lesson_view.py — Theory / Practice tabs for the active lesson.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .practice_view import PracticeView
from .theory_view import TheoryView


class LessonView(QWidget):
    exerciseSolved = Signal(str, str)
    exerciseFailed = Signal(str)

    def __init__(self, i18n, progress: dict, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._lesson = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.theory = TheoryView()
        self.practice = PracticeView(i18n, progress)
        self.tabs.addTab(self.theory, i18n.t("tab_theory"))
        self.tabs.addTab(self.practice, i18n.t("tab_practice"))
        layout.addWidget(self.tabs)

        self.practice.exerciseSolved.connect(self.exerciseSolved)
        self.practice.exerciseFailed.connect(self.exerciseFailed)

    def set_lesson(self, lesson, lang: str) -> None:
        self._lesson = lesson
        self.theory.render_blocks(lesson.theory_blocks(lang))
        self.practice.set_lesson(lesson, lang)
        self.tabs.setCurrentIndex(0)

    def show_practice(self) -> None:
        self.tabs.setCurrentIndex(1)

    def retranslate(self) -> None:
        self.tabs.setTabText(0, self.i18n.t("tab_theory"))
        self.tabs.setTabText(1, self.i18n.t("tab_practice"))
        if self._lesson is not None:
            self.theory.render_blocks(self._lesson.theory_blocks(self.i18n.lang))
            self.practice.retranslate()

    def refresh_theme(self) -> None:
        self.theory.apply_css()
        if self._lesson is not None:
            self.theory.render_blocks(self._lesson.theory_blocks(self.i18n.lang))
        self.practice.refresh_theme()

    def set_content_font_size(self, pt: int) -> None:
        from .. import theme
        f = theme.get_mono_font(pt)
        self.theory.setFont(f)
        self.practice.editor.set_font_size(pt)
        self.practice.console.setFont(f)
        if self._lesson is not None:
            self.theory.render_blocks(self._lesson.theory_blocks(self.i18n.lang))

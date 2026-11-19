"""
sidebar.py — navegación por módulos y lecciones (árbol) con marcas de progreso.
sidebar.py — module/lesson navigation tree with progress checkmarks.
"""
from __future__ import annotations

import unicodedata

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QProgressBar, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .. import progress as prog
from .. import theme

_DATA_ROLE = Qt.UserRole
_SEARCH_ROLE = Qt.UserRole + 1


class Sidebar(QWidget):
    lessonSelected = Signal(int, int)  # (módulo, lección)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        banner = QLabel("PyQuest  >_")
        banner.setObjectName("banner")
        f = theme.get_mono_font(16)
        f.setBold(True)
        banner.setFont(f)
        self._subtitle = QLabel("// aprende python")
        self._subtitle.setObjectName("section")

        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText("Buscar…")
        self.search.textChanged.connect(self._on_search)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.itemClicked.connect(self._on_item_clicked)

        self._progress = QLabel("")
        self._progress.setObjectName("section")

        self.bar = QProgressBar()
        self.bar.setObjectName("progress")
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(True)
        self.bar.setFormat("%p%")

        layout.addWidget(banner)
        layout.addWidget(self._subtitle)
        layout.addWidget(self.search)
        layout.addWidget(self.tree, 1)
        layout.addWidget(self._progress)
        layout.addWidget(self.bar)

    def set_subtitle(self, text: str) -> None:
        self._subtitle.setText(text)

    def set_progress(self, text: str) -> None:
        self._progress.setText(text)

    def set_progress_value(self, done: int, total: int) -> None:
        self.bar.setValue(round(done * 100 / total) if total else 0)

    def set_search_placeholder(self, text: str) -> None:
        self.search.setPlaceholderText(text)

    def populate(self, course, lang: str, progress: dict) -> None:
        self.tree.clear()
        for mi, module in enumerate(course.modules):
            m_total = sum(len(les.exercises) for les in module.lessons)
            m_done = sum(1 for les in module.lessons for ex in les.exercises
                         if prog.is_exercise_completed(progress, ex.id))
            suffix = f"  ({m_done}/{m_total})" if m_total else ""
            top = QTreeWidgetItem([f"{mi + 1}. {module.title_text(lang)}{suffix}"])
            top.setData(0, _DATA_ROLE, None)
            top.setForeground(0, _brush(theme.FG_BRIGHT))
            self.tree.addTopLevelItem(top)
            for li, lesson in enumerate(module.lessons):
                done = prog.is_lesson_completed(progress, lesson.id)
                star = "★ " if prog.is_bookmarked(progress, lesson.id) else ""
                mark = "✔ " if done else "• "
                child = QTreeWidgetItem([f"{star}{mark}{lesson.title_text(lang)}"])
                child.setData(0, _DATA_ROLE, (mi, li))
                child.setData(0, _SEARCH_ROLE, _search_text(
                    lesson, f"{module.title_text('es')} {module.title_text('en')}"))
                if done:
                    child.setForeground(0, _brush(theme.OK))
                top.addChild(child)
            top.setExpanded(True)
        if self.search.text().strip():
            self._on_search(self.search.text())

    def refresh_marks(self, course, lang: str, progress: dict) -> None:
        self.populate(course, lang, progress)

    def select_first_lesson(self) -> None:
        top = self.tree.topLevelItem(0)
        if top and top.childCount():
            child = top.child(0)
            self.tree.setCurrentItem(child)
            self._on_item_clicked(child, 0)

    def select_lesson(self, mi: int, li: int) -> bool:
        top = self.tree.topLevelItem(mi)
        if top and 0 <= li < top.childCount():
            child = top.child(li)
            self.tree.setCurrentItem(child)
            self._on_item_clicked(child, 0)
            return True
        return False

    def _on_search(self, text: str) -> None:
        from PySide6.QtGui import QBrush
        tokens = _normaliza(text.strip()).split()
        resalte = _brush(theme.SELECTION)
        limpio = QBrush()
        for mi in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(mi)
            visibles = 0
            for li in range(top.childCount()):
                child = top.child(li)
                st = child.data(0, _SEARCH_ROLE) or ""
                match = (not tokens) or all(tok in st for tok in tokens)
                child.setHidden(not match)
                child.setBackground(0, resalte if (tokens and match) else limpio)
                if match:
                    visibles += 1
            top.setHidden(bool(tokens) and visibles == 0)
            if tokens:
                top.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        data = item.data(0, _DATA_ROLE)
        if data is not None:
            self.lessonSelected.emit(data[0], data[1])


def _normaliza(s: str) -> str:
    """Minúsculas y sin acentos, para que la búsqueda no dependa de tildes."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def _search_text(lesson, extra: str = "") -> str:
    """Texto buscable de una lección: módulo + títulos + teoría + enunciados (ES/EN)."""
    parts = [extra, lesson.title_text("es"), lesson.title_text("en")]
    for lang in ("es", "en"):
        for b in lesson.theory_blocks(lang):
            v = b.get("value", "")
            parts.append(v if isinstance(v, str) else " ".join(str(x) for x in v))
    for ex in lesson.exercises:
        parts.append(ex.prompt_text("es"))
        parts.append(ex.prompt_text("en"))
    return _normaliza(" ".join(parts))


def _brush(color: str):
    from PySide6.QtGui import QBrush, QColor
    return QBrush(QColor(color))

"""
stats.py — diálogo "Mi progreso": gráfica + resumen global y desglose por módulo.
stats.py — "My progress" dialog: chart + overall summary and per-module breakdown.
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QWidget

from .. import progress as prog
from .. import theme

_BAR_WIDTH = 10


class _ChartProgreso(QWidget):
    """Mini-gráfica: una barra vertical por módulo, alta según su % completado."""

    def __init__(self, pcts, parent=None):
        super().__init__(parent)
        self._pcts = list(pcts)
        self.setMinimumHeight(96)

    def set_pcts(self, pcts) -> None:
        self._pcts = list(pcts)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w, hh = self.width(), self.height()
        p.fillRect(0, 0, w, hh, QColor(theme.BG_ALT))
        p.setPen(QColor(theme.BORDER))
        p.drawRect(0, 0, w - 1, hh - 1)
        n = len(self._pcts)
        if not n:
            p.end()
            return
        margen = 8
        bw = (w - 2 * margen) / n
        base = hh - margen
        alto = hh - 2 * margen
        for i, pct in enumerate(self._pcts):
            x = margen + i * bw
            bh = alto * max(0, min(100, pct)) / 100
            color = QColor(theme.OK) if pct >= 100 else QColor(theme.FG_DIM)
            p.fillRect(int(x), int(base - bh), max(1, int(bw) - 1), int(bh), color)
        p.end()


class StatsDialog(QDialog):
    def __init__(self, i18n, course, progress: dict, font_pt: int = 11, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setWindowTitle(i18n.t("stats_title"))
        self.resize(560, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        pcts = []
        for m in course.modules:
            tot = sum(len(les.exercises) for les in m.lessons)
            d = sum(1 for les in m.lessons for ex in les.exercises
                    if prog.is_exercise_completed(progress, ex.id))
            pcts.append(round(d * 100 / tot) if tot else 0)
        self.chart = _ChartProgreso(pcts)
        layout.addWidget(self.chart)

        self.view = QTextEdit()
        self.view.setReadOnly(True)
        self.view.setFont(theme.get_mono_font(font_pt))
        self.view.setStyleSheet(
            f"background: {theme.BG_ALT}; color: {theme.FG};"
            f" border: 1px solid {theme.BORDER}; border-radius: 4px;"
        )
        layout.addWidget(self.view, 1)
        self.view.setPlainText(self._build_text(course, progress))

    def _build_text(self, course, progress: dict) -> str:
        lang = self.i18n.lang
        t = self.i18n.t
        lines: list[str] = []
        total = done = 0
        body: list[str] = []
        for i, m in enumerate(course.modules, 1):
            m_tot = sum(len(les.exercises) for les in m.lessons)
            m_done = sum(
                1 for les in m.lessons for ex in les.exercises
                if prog.is_exercise_completed(progress, ex.id)
            )
            total += m_tot
            done += m_done
            filled = round(m_done * _BAR_WIDTH / m_tot) if m_tot else 0
            bar = "#" * filled + "·" * (_BAR_WIDTH - filled)
            title = m.title_text(lang)
            title = (title[:24] + "…") if len(title) > 25 else title.ljust(25)
            body.append(f"{i:2d}. {title} [{bar}] {m_done:>2}/{m_tot}")

        pct = round(done * 100 / total) if total else 0
        xp = progress.get("xp", 0)
        streak = progress.get("streak", 0)
        ach = len(progress.get("achievements", []))
        ach_total = len(prog.all_achievements())

        lines.append(f"{t('progress')}: {done}/{total}  ({pct}%)")
        lines.append(
            f"{t('xp')} {xp}   ·   {t('streak')} {streak} {t('days')}"
            f"   ·   {t('menu_achievements')} {ach}/{ach_total}"
        )
        n_fails = sum(1 for v in progress.get("fails", {}).values() if v > 0)
        n_marc = len(progress.get("bookmarks", []))
        lines.append(f"{t('stats_fails')}: {n_fails}   ·   {t('menu_bookmark')}: {n_marc}")
        lines.append("")
        lines.append("─" * 46)
        lines.extend(body)
        return "\n".join(lines)

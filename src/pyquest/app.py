"""
app.py — ventana principal y arranque de la aplicación.
app.py — main window and application bootstrap.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QMainWindow, QMessageBox, QSplitter, QVBoxLayout, QWidget,
)

from . import __app_name__, __version__
from . import content as content_mod
from . import progress as prog
from . import theme
from .i18n import I18N
from .util import resource_path
from .widgets.lesson_view import LessonView
from .widgets.overlay import ScanlineOverlay
from .widgets.playground import PlaygroundWindow
from .widgets.stats import StatsDialog
from .widgets.sidebar import Sidebar


def _app_icon():
    """Carga el icono de la app (assets/icon.png) si existe."""
    try:
        p = resource_path("assets", "icon.png")
        if p.exists():
            return QIcon(str(p))
    except Exception:
        pass
    return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.progress = prog.load()
        self.i18n = I18N(self.progress.get("language", "es"))
        theme.set_theme(self.progress.get("theme", "green"))
        self.content_pt = self.progress.get("font_pt", theme.FONT_SIZE)
        self.current = (0, 0)
        self.playground = None

        icon = _app_icon()
        if icon is not None:
            self.setWindowIcon(icon)

        try:
            self.course = content_mod.load_course()
        except Exception as e:  # contenido ausente/corrupto: no romper la app
            self.course = content_mod.Course()
            QMessageBox.warning(self, __app_name__,
                                f"No se pudo cargar el contenido:\n{e}")

        self._build_ui()
        self._build_menus()
        self._populate()
        self.setWindowTitle(self.i18n.t("app_title"))
        win = self.progress.get("window") or [1180, 760]
        try:
            self.resize(int(win[0]), int(win[1]))
        except (TypeError, ValueError, IndexError):
            self.resize(1180, 760)
        QApplication.instance().setStyleSheet(theme.build_qss())
        self.lesson_view.set_content_font_size(self.content_pt)

    # ------------------------------------------------------------------ #
    def _build_ui(self):
        self.sidebar = Sidebar()
        self.sidebar.lessonSelected.connect(self.open_lesson)

        self.lesson_view = LessonView(self.i18n, self.progress)
        self.lesson_view.exerciseSolved.connect(self.on_exercise_solved)
        self.lesson_view.exerciseFailed.connect(self.on_exercise_failed)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.lesson_view)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([300, 880])

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.splitter)
        self.setCentralWidget(central)

        # superposición CRT por encima de todo
        self.overlay = ScanlineOverlay(central)
        self.overlay.set_enabled(self.progress.get("scanlines", True))

        self.statusBar().showMessage(self.i18n.t("ready"))
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.sidebar.search.setFocus())

    def _build_menus(self):
        mb = self.menuBar()

        self.menu_file = mb.addMenu(self.i18n.t("menu_file"))
        self.act_export = QAction(self.i18n.t("menu_export"), self)
        self.act_export.triggered.connect(self.export_progress)
        self.menu_file.addAction(self.act_export)
        self.act_import = QAction(self.i18n.t("menu_import"), self)
        self.act_import.triggered.connect(self.import_progress)
        self.menu_file.addAction(self.act_import)
        self.menu_file.addSeparator()
        self.act_reset = QAction(self.i18n.t("menu_reset_progress"), self)
        self.act_reset.triggered.connect(self.reset_progress)
        self.menu_file.addAction(self.act_reset)
        self.menu_file.addSeparator()
        self.act_exit = QAction(self.i18n.t("menu_exit"), self)
        self.act_exit.triggered.connect(self.close)
        self.menu_file.addAction(self.act_exit)

        self.menu_view = mb.addMenu(self.i18n.t("menu_view"))
        self.act_scan = QAction(self.i18n.t("toggle_scanlines"), self, checkable=True)
        self.act_scan.setChecked(self.progress.get("scanlines", True))
        self.act_scan.toggled.connect(self.toggle_scanlines)
        self.menu_view.addAction(self.act_scan)

        self.menu_lang = self.menu_view.addMenu(self.i18n.t("menu_lang"))
        group = QActionGroup(self)
        self.act_es = QAction(self.i18n.t("lang_es"), self, checkable=True)
        self.act_en = QAction(self.i18n.t("lang_en"), self, checkable=True)
        self.act_es.triggered.connect(lambda: self.set_language("es"))
        self.act_en.triggered.connect(lambda: self.set_language("en"))
        for a in (self.act_es, self.act_en):
            group.addAction(a)
            self.menu_lang.addAction(a)
        (self.act_es if self.i18n.lang == "es" else self.act_en).setChecked(True)

        self.menu_theme = self.menu_view.addMenu(self.i18n.t("menu_theme"))
        theme_group = QActionGroup(self)
        self.theme_actions = {}
        for key, lab in (("green", "theme_green"), ("amber", "theme_amber"),
                         ("dos", "theme_dos"), ("light", "theme_light")):
            act = QAction(self.i18n.t(lab), self, checkable=True)
            act.triggered.connect(lambda _checked=False, k=key: self.set_theme(k))
            theme_group.addAction(act)
            self.menu_theme.addAction(act)
            self.theme_actions[key] = act
        self.theme_actions.get(theme.current_theme, self.theme_actions["green"]).setChecked(True)

        self.menu_view.addSeparator()
        self.act_zoom_in = QAction(self.i18n.t("menu_zoom_in"), self)
        self.act_zoom_in.setShortcut("Ctrl++")
        self.act_zoom_in.triggered.connect(self.zoom_in)
        self.act_zoom_out = QAction(self.i18n.t("menu_zoom_out"), self)
        self.act_zoom_out.setShortcut("Ctrl+-")
        self.act_zoom_out.triggered.connect(self.zoom_out)
        self.act_zoom_reset = QAction(self.i18n.t("menu_zoom_reset"), self)
        self.act_zoom_reset.setShortcut("Ctrl+0")
        self.act_zoom_reset.triggered.connect(self.zoom_reset)
        for _a in (self.act_zoom_in, self.act_zoom_out, self.act_zoom_reset):
            self.menu_view.addAction(_a)

        self.menu_view.addSeparator()
        self.act_playground = QAction(self.i18n.t("menu_playground"), self)
        self.act_playground.setShortcut("Ctrl+P")
        self.act_playground.triggered.connect(self.open_playground)
        self.menu_view.addAction(self.act_playground)
        self.act_stats = QAction(self.i18n.t("menu_stats"), self)
        self.act_stats.triggered.connect(self.open_stats)
        self.menu_view.addAction(self.act_stats)
        self.act_next = QAction(self.i18n.t("menu_next"), self)
        self.act_next.setShortcut("Ctrl+J")
        self.act_next.triggered.connect(self.goto_next_pending)
        self.menu_view.addAction(self.act_next)
        self.act_review = QAction(self.i18n.t("menu_review"), self)
        self.act_review.triggered.connect(self.goto_review)
        self.menu_view.addAction(self.act_review)
        self.act_bookmark = QAction(self.i18n.t("menu_bookmark"), self)
        self.act_bookmark.setShortcut("Ctrl+D")
        self.act_bookmark.triggered.connect(self.toggle_bookmark)
        self.menu_view.addAction(self.act_bookmark)

        self.menu_course = mb.addMenu(self.i18n.t("menu_course"))
        self.act_exam = QAction(self.i18n.t("menu_exam"), self)
        self.act_exam.triggered.connect(self.open_exam)
        self.menu_course.addAction(self.act_exam)

        self.menu_help = mb.addMenu(self.i18n.t("menu_help"))
        self.act_achievements = QAction(self.i18n.t("menu_achievements"), self)
        self.act_achievements.triggered.connect(self.show_achievements)
        self.menu_help.addAction(self.act_achievements)
        self.act_shortcuts = QAction(self.i18n.t("menu_shortcuts"), self)
        self.act_shortcuts.triggered.connect(self.show_shortcuts)
        self.menu_help.addAction(self.act_shortcuts)
        self.act_about = QAction(self.i18n.t("menu_about"), self)
        self.act_about.triggered.connect(self.show_about)
        self.menu_help.addAction(self.act_about)

    # ------------------------------------------------------------------ #
    def _populate(self):
        sub = "// aprende python" if self.i18n.lang == "es" else "// learn python"
        self.sidebar.set_subtitle(sub)
        self.sidebar.set_search_placeholder(self.i18n.t("search_placeholder"))
        self.sidebar.populate(self.course, self.i18n.lang, self.progress)
        self._update_progress()
        if self.course.modules:
            ll = self.progress.get("last_lesson") or [0, 0]
            mi, li = (ll if isinstance(ll, list) and len(ll) == 2 else [0, 0])
            if not self.sidebar.select_lesson(mi, li):
                self.sidebar.select_first_lesson()

    def _lesson_at(self, mi, li):
        try:
            return self.course.modules[mi].lessons[li]
        except (IndexError, AttributeError):
            return None

    def _lesson_of_exercise(self, exercise_id: str):
        for _m, ls in self.course.all_lessons():
            if any(ex.id == exercise_id for ex in ls.exercises):
                return ls
        return None

    def open_lesson(self, mi: int, li: int):
        lesson = self._lesson_at(mi, li)
        if lesson is None:
            return
        self.current = (mi, li)
        self.progress["last_lesson"] = [mi, li]
        prog.save(self.progress)
        self.lesson_view.set_lesson(lesson, self.i18n.lang)
        self.statusBar().showMessage(lesson.title_text(self.i18n.lang))

    def on_exercise_solved(self, exercise_id: str, code: str):
        is_new = not prog.is_exercise_completed(self.progress, exercise_id)
        # Si vio la solución antes de resolverlo, cuenta como resuelto pero sin XP.
        xp_gained = 0 if prog.solution_was_viewed(self.progress, exercise_id) else prog.XP_PER_EXERCISE
        prog.mark_exercise_completed(self.progress, exercise_id, code)
        nuevos_logros = []
        if is_new:
            self.progress["xp"] = self.progress.get("xp", 0) + xp_gained
            prog.register_activity(self.progress)
        # ¿lección completa? (todos sus ejercicios resueltos). Se busca la lección
        # del ejercicio, no la abierta: el usuario pudo cambiar mientras se comprobaba.
        lesson = self._lesson_of_exercise(exercise_id)
        if lesson and lesson.exercises:
            if all(prog.is_exercise_completed(self.progress, e.id) for e in lesson.exercises):
                prog.mark_lesson_completed(self.progress, lesson.id)
        if is_new:
            done = sum(1 for _m, ls in self.course.all_lessons() for ex in ls.exercises
                       if prog.is_exercise_completed(self.progress, ex.id))
            total = sum(len(ls.exercises) for _m, ls in self.course.all_lessons())
            nuevos_logros = prog.check_new_achievements(self.progress, done, total)
        prog.save(self.progress)
        self.sidebar.refresh_marks(self.course, self.i18n.lang, self.progress)
        self._update_progress()
        self._reselect_current()
        if is_new and self._showing_exercise(exercise_id):
            self._celebrate(nuevos_logros, xp_gained)

    def _showing_exercise(self, exercise_id: str) -> bool:
        cur = self.lesson_view.practice._current()
        return cur is not None and cur.id == exercise_id

    def _celebrate(self, nuevos_logros, xp_gained: int = prog.XP_PER_EXERCISE):
        """Feedback de gamificación al resolver un ejercicio nuevo."""
        console = self.lesson_view.practice.console
        if xp_gained:
            self.statusBar().showMessage(f"+{xp_gained} XP")
            console.write_ok(f"  +{xp_gained} XP")
        else:
            self.statusBar().showMessage(self.i18n.t("no_xp_solution"))
            console.write_dim("  " + self.i18n.t("no_xp_solution"))
        for name in nuevos_logros:
            txt = name.get(self.i18n.lang, name.get("es"))
            console.write_info(f"  ★ {self.i18n.t('achievement')}: {txt}")

    def _update_progress(self):
        # Progreso por EJERCICIOS: sube cada vez que se resuelve uno (no solo al
        # completar la lección entera).
        total = sum(len(ls.exercises) for _m, ls in self.course.all_lessons())
        done = sum(1 for _m, ls in self.course.all_lessons() for ex in ls.exercises
                   if prog.is_exercise_completed(self.progress, ex.id))
        pct = round(done * 100 / total) if total else 0
        xp = self.progress.get("xp", 0)
        streak = self.progress.get("streak", 0)
        line1 = f"{self.i18n.t('progress')}: {done}/{total} · {pct}%"
        line2 = f"{self.i18n.t('xp')} {xp} · {self.i18n.t('streak')} {streak} {self.i18n.t('days')}"
        self.sidebar.set_progress_value(done, total)
        self.sidebar.set_progress(line1 + "\n" + line2)

    def reset_progress(self):
        if QMessageBox.question(self, __app_name__,
                                self.i18n.t("confirm_reset")) != QMessageBox.Yes:
            return
        # el código que hay ahora en el editor no debe sobrevivir como borrador
        self.lesson_view.practice.discard_editor()
        prog.reset(self.progress)  # en sitio: la vista comparte la referencia
        prog.save(self.progress)
        self.sidebar.refresh_marks(self.course, self.i18n.lang, self.progress)
        self._update_progress()
        self.open_lesson(*self.current)

    # ------------------------------------------------------------------ #
    def set_language(self, lang: str):
        if lang == self.i18n.lang:
            return
        self.i18n.set_language(lang)
        self.progress["language"] = lang
        prog.save(self.progress)
        self._retranslate_menus()
        self._populate()
        self.lesson_view.retranslate()
        if self.playground is not None:
            self.playground.retranslate()
        self._reselect_current()

    def _retranslate_menus(self):
        self.setWindowTitle(self.i18n.t("app_title"))
        self.menu_file.setTitle(self.i18n.t("menu_file"))
        self.act_export.setText(self.i18n.t("menu_export"))
        self.act_import.setText(self.i18n.t("menu_import"))
        self.act_reset.setText(self.i18n.t("menu_reset_progress"))
        self.act_exit.setText(self.i18n.t("menu_exit"))
        self.menu_view.setTitle(self.i18n.t("menu_view"))
        self.act_scan.setText(self.i18n.t("toggle_scanlines"))
        self.menu_lang.setTitle(self.i18n.t("menu_lang"))
        self.act_es.setText(self.i18n.t("lang_es"))
        self.act_en.setText(self.i18n.t("lang_en"))
        self.menu_theme.setTitle(self.i18n.t("menu_theme"))
        self.theme_actions["green"].setText(self.i18n.t("theme_green"))
        self.theme_actions["amber"].setText(self.i18n.t("theme_amber"))
        self.theme_actions["dos"].setText(self.i18n.t("theme_dos"))
        self.theme_actions["light"].setText(self.i18n.t("theme_light"))
        self.act_zoom_in.setText(self.i18n.t("menu_zoom_in"))
        self.act_zoom_out.setText(self.i18n.t("menu_zoom_out"))
        self.act_zoom_reset.setText(self.i18n.t("menu_zoom_reset"))
        self.act_playground.setText(self.i18n.t("menu_playground"))
        self.act_stats.setText(self.i18n.t("menu_stats"))
        self.act_next.setText(self.i18n.t("menu_next"))
        self.act_review.setText(self.i18n.t("menu_review"))
        self.act_bookmark.setText(self.i18n.t("menu_bookmark"))
        self.menu_course.setTitle(self.i18n.t("menu_course"))
        self.act_exam.setText(self.i18n.t("menu_exam"))
        self.menu_help.setTitle(self.i18n.t("menu_help"))
        self.act_achievements.setText(self.i18n.t("menu_achievements"))
        self.act_shortcuts.setText(self.i18n.t("menu_shortcuts"))
        self.act_about.setText(self.i18n.t("menu_about"))

    def _apply_settings(self):
        """Lleva a la interfaz las preferencias de ``self.progress`` (tras importar)."""
        theme.set_theme(self.progress["theme"])
        QApplication.instance().setStyleSheet(theme.build_qss())
        self.theme_actions.get(theme.current_theme, self.theme_actions["green"]).setChecked(True)
        self.act_scan.blockSignals(True)  # sin disparar toggle_scanlines (guardaría de nuevo)
        self.act_scan.setChecked(self.progress["scanlines"])
        self.act_scan.blockSignals(False)
        self.overlay.set_enabled(self.progress["scanlines"])
        self.i18n.set_language(self.progress["language"])
        (self.act_es if self.i18n.lang == "es" else self.act_en).setChecked(True)
        self._retranslate_menus()
        self.content_pt = self.progress["font_pt"]
        self.lesson_view.refresh_theme()
        self.lesson_view.retranslate()
        self.lesson_view.set_content_font_size(self.content_pt)
        if self.playground is not None:
            self.playground.retranslate()
            self.playground.refresh_theme()
        self._populate()

    def _reselect_current(self):
        mi, li = self.current
        # vuelve a marcar la lección activa en el árbol
        top = self.sidebar.tree.topLevelItem(mi)
        if top and li < top.childCount():
            self.sidebar.tree.setCurrentItem(top.child(li))

    def toggle_scanlines(self, on: bool):
        self.overlay.set_enabled(on)
        self.progress["scanlines"] = on
        prog.save(self.progress)

    def set_theme(self, name: str):
        theme.set_theme(name)
        self.progress["theme"] = name
        prog.save(self.progress)
        QApplication.instance().setStyleSheet(theme.build_qss())
        self.lesson_view.refresh_theme()
        if self.playground is not None:
            self.playground.refresh_theme()
        self.sidebar.populate(self.course, self.i18n.lang, self.progress)
        self._update_progress()
        self._reselect_current()

    def zoom_in(self):
        self._set_font(self.content_pt + 1)

    def zoom_out(self):
        self._set_font(self.content_pt - 1)

    def zoom_reset(self):
        self._set_font(theme.FONT_SIZE)

    def _set_font(self, pt: int):
        self.content_pt = max(8, min(24, pt))
        self.progress["font_pt"] = self.content_pt
        prog.save(self.progress)
        self.lesson_view.set_content_font_size(self.content_pt)

    def show_about(self):
        if self.i18n.lang == "es":
            msg = (f"{__app_name__} v{__version__}\n\n"
                   "Aprende Python con teoría + práctica, al estilo de una "
                   "terminal retro.\nMotor de corrección: análisis estático + "
                   "ejecución real con tests.\n\nHecho por Alex García González.")
        else:
            msg = (f"{__app_name__} v{__version__}\n\n"
                   "Learn Python with theory + practice, retro-terminal style.\n"
                   "Grading engine: static analysis + real execution with tests.\n\nMade by Alex García González.")
        QMessageBox.about(self, __app_name__, msg)

    def show_achievements(self):
        have = set(self.progress.get("achievements", []))
        lang = self.i18n.lang
        todos = prog.all_achievements()
        lineas = []
        for aid, names in todos:
            marca = "[x]" if aid in have else "[ ]"
            lineas.append(f"{marca} {names.get(lang, names.get('es'))}")
        cab = f"{self.i18n.t('menu_achievements')}: {len(have)}/{len(todos)}\n\n"
        QMessageBox.information(self, self.i18n.t("menu_achievements"), cab + "\n".join(lineas))

    def open_playground(self):
        if self.playground is None:
            self.playground = PlaygroundWindow(self.i18n, self.content_pt, self)
        self.playground.show()
        self.playground.raise_()
        self.playground.activateWindow()

    def open_stats(self):
        StatsDialog(self.i18n, self.course, self.progress, self.content_pt, self).exec()

    def goto_next_pending(self):
        for mi, m in enumerate(self.course.modules):
            for li, lesson in enumerate(m.lessons):
                for ei, ex in enumerate(lesson.exercises):
                    if not prog.is_exercise_completed(self.progress, ex.id):
                        self.open_lesson(mi, li)
                        self.lesson_view.show_practice()
                        self.lesson_view.practice.goto_exercise(ei)
                        self._reselect_current()
                        return
        QMessageBox.information(self, __app_name__, self.i18n.t("all_done"))

    def on_exercise_failed(self, exercise_id: str):
        prog.record_fail(self.progress, exercise_id)
        prog.save(self.progress)

    def goto_review(self):
        fails = self.progress.get("fails", {})
        cands = []
        for mi, m in enumerate(self.course.modules):
            for li, lesson in enumerate(m.lessons):
                for ei, ex in enumerate(lesson.exercises):
                    if fails.get(ex.id, 0) > 0:
                        pendiente = 0 if prog.is_exercise_completed(self.progress, ex.id) else 1
                        cands.append((pendiente, fails[ex.id], mi, li, ei))
        if not cands:
            QMessageBox.information(self, __app_name__, self.i18n.t("nothing_to_review"))
            return
        cands.sort(key=lambda c: (-c[0], -c[1], c[2], c[3], c[4]))
        _, _, mi, li, ei = cands[0]
        self.open_lesson(mi, li)
        self.lesson_view.show_practice()
        self.lesson_view.practice.goto_exercise(ei)
        self._reselect_current()

    def toggle_bookmark(self):
        mi, li = self.current
        lesson = self._lesson_at(mi, li)
        if lesson is None:
            return
        marcada = prog.toggle_bookmark(self.progress, lesson.id)
        prog.save(self.progress)
        self.sidebar.refresh_marks(self.course, self.i18n.lang, self.progress)
        self._reselect_current()
        self.statusBar().showMessage(self.i18n.t("bookmarked" if marcada else "unbookmarked"))

    def open_exam(self):
        from .widgets.quiz import ExamDialog
        ExamDialog(self.i18n, self.progress, self).exec()
        prog.save(self.progress)

    def show_shortcuts(self):
        if self.i18n.lang == "es":
            msg = ("Atajos de teclado:\n\n"
                   "Ctrl+Intro / Ctrl+R : comprobar / ejecutar\n"
                   "Ctrl+J : ir al siguiente ejercicio pendiente\n"
                   "Ctrl+F : buscar lección\n"
                   "Ctrl+D : marcar/desmarcar lección\n"
                   "Ctrl+P : abrir Playground\n"
                   "Ctrl++ / Ctrl+- / Ctrl+0 : tamaño de fuente\n"
                   "Flechas arriba/abajo (en la entrada) : historial")
        else:
            msg = ("Keyboard shortcuts:\n\n"
                   "Ctrl+Enter / Ctrl+R : check / run\n"
                   "Ctrl+J : go to next pending exercise\n"
                   "Ctrl+F : search lesson\n"
                   "Ctrl+D : toggle bookmark\n"
                   "Ctrl+P : open Playground\n"
                   "Ctrl++ / Ctrl+- / Ctrl+0 : font size\n"
                   "Up/Down arrows (in input) : history")
        QMessageBox.information(self, self.i18n.t("menu_shortcuts"), msg)

    def export_progress(self):
        import json
        path, _ = QFileDialog.getSaveFileName(
            self, self.i18n.t("menu_export"), "pyquest_progreso.json", "JSON (*.json)")
        if not path:
            return
        self.lesson_view.practice.stash_draft()  # incluye el código que hay ahora en el editor
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
            self.statusBar().showMessage(self.i18n.t("export_ok"))
        except OSError as e:
            QMessageBox.warning(self, __app_name__, str(e))

    def import_progress(self):
        path, _ = QFileDialog.getOpenFileName(
            self, self.i18n.t("menu_import"), "", "JSON (*.json)")
        if not path:
            return
        if self.load_progress_file(path):
            self.statusBar().showMessage(self.i18n.t("import_ok"))
        else:
            QMessageBox.warning(self, __app_name__, self.i18n.t("import_err"))

    def load_progress_file(self, path: str) -> bool:
        """Sustituye el progreso por el de ``path`` y lo aplica a toda la interfaz."""
        import json
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, ValueError):  # JSONDecodeError/UnicodeDecodeError son ValueError
            return False
        if not isinstance(raw, dict):
            return False
        # el código del editor pertenece al progreso anterior, no al importado
        self.lesson_view.practice.discard_editor()
        self.progress.clear()  # en sitio: la vista comparte la referencia
        self.progress.update(prog.normalize(raw))
        prog.save(self.progress)
        self._apply_settings()
        return True

    # ------------------------------------------------------------------ #
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "overlay"):
            self.overlay.setGeometry(self.centralWidget().rect())
            self.overlay.raise_()

    def closeEvent(self, event):
        self.lesson_view.practice.shutdown()
        self.lesson_view.practice.stash_draft()
        self.progress["window"] = [self.width(), self.height()]
        prog.save(self.progress)
        super().closeEvent(event)


def run_app(argv: list[str]) -> int:
    app = QApplication(argv)
    app.setApplicationName(__app_name__)
    app.setOrganizationName(__app_name__)
    app.setFont(theme.get_mono_font())
    app.setStyleSheet(theme.build_qss())
    icon = _app_icon()
    if icon is not None:
        app.setWindowIcon(icon)
    win = MainWindow()
    win.show()
    return app.exec()

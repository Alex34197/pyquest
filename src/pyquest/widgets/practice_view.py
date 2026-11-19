"""
practice_view.py — zona de práctica: enunciado, editor, botones y consola.
practice_view.py — practice area: task, editor, buttons and console.

La ejecución/corrección se hace en un hilo (RunnerWorker) para no congelar la
interfaz mientras corre el código del usuario.
"""
from __future__ import annotations

import html
import re

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QSplitter, QVBoxLayout, QWidget,
)

from .. import progress as prog
from .. import runner
from .code_editor import CodeEditor
from .console import ConsoleOutput
from .history_input import HistoryInput
from .interactive import InteractiveSession


def _md_inline(text: str) -> str:
    """Convierte `código` y **negrita** a HTML para mostrar el enunciado."""
    s = html.escape(text)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    return s


class RunnerWorker(QThread):
    """Ejecuta (run) o corrige (check) el código del usuario en segundo plano."""
    finished_run = Signal(object)              # RunResult
    finished_check = Signal(object, str, str)  # Evaluation, exercise_id, código comprobado

    def __init__(self, mode: str, source: str, exercise: dict, exercise_id: str = ""):
        super().__init__()
        self.mode = mode
        self.source = source
        self.exercise = exercise
        # Se guarda QUÉ ejercicio y QUÉ código se comprobó: cuando llega el
        # resultado el usuario puede estar ya en otro ejercicio o lección.
        self.exercise_id = exercise_id

    def run(self):
        try:
            if self.mode == "run":
                self.finished_run.emit(runner.run_code(self.source))
            else:
                ev = runner.evaluate(self.source, self.exercise)
                self.finished_check.emit(ev, self.exercise_id, self.source)
        except Exception as e:  # red de seguridad: nunca tumbar el hilo
            rr = runner.RunResult(stderr=str(e), exit_code=1)
            if self.mode == "run":
                self.finished_run.emit(rr)
            else:
                ev = runner.Evaluation(run=rr)
                self.finished_check.emit(ev, self.exercise_id, self.source)


class PracticeView(QWidget):
    exerciseSolved = Signal(str, str)  # (exercise_id, code)
    exerciseFailed = Signal(str)       # (exercise_id) tras fallar la comprobación

    def __init__(self, i18n, progress: dict, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.progress = progress
        self.lesson = None
        self.exercises: list = []
        self.idx = 0
        self.hint_idx = 0
        self._worker: RunnerWorker | None = None
        self._busy = False  # True mientras se está comprobando un ejercicio

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        # cabecera: navegación entre ejercicios
        header = QHBoxLayout()
        self.lbl_counter = QLabel("")
        self.lbl_counter.setObjectName("section")
        self.btn_prev = QPushButton("◀")
        self.btn_next = QPushButton("▶")
        self.btn_prev.setMaximumWidth(44)
        self.btn_next.setMaximumWidth(44)
        self.btn_prev.clicked.connect(lambda: self._go(-1))
        self.btn_next.clicked.connect(lambda: self._go(1))
        header.addWidget(self.lbl_counter)
        header.addStretch(1)
        header.addWidget(self.btn_prev)
        header.addWidget(self.btn_next)
        root.addLayout(header)

        # enunciado
        self.lbl_prompt = QLabel("")
        self.lbl_prompt.setObjectName("prompt")
        self.lbl_prompt.setWordWrap(True)
        self.lbl_prompt.setTextFormat(Qt.RichText)
        root.addWidget(self.lbl_prompt)

        # editor + consola en un splitter vertical
        splitter = QSplitter(Qt.Vertical)
        self.editor = CodeEditor()
        self.console = ConsoleOutput()
        splitter.addWidget(self.editor)
        splitter.addWidget(self.console)
        splitter.setSizes([320, 160])
        root.addWidget(splitter, 1)

        # entrada interactiva (para input() en vivo)
        in_row = QHBoxLayout()
        in_row.addWidget(QLabel(">"))
        self.input_line = HistoryInput()
        self.input_line.setObjectName("input_line")
        self.input_line.setPlaceholderText(self.i18n.t("input_placeholder"))
        self.input_line.setEnabled(False)
        self.input_line.returnPressed.connect(self._send_input)
        in_row.addWidget(self.input_line, 1)
        root.addLayout(in_row)

        # sesión interactiva (QProcess): ejecuta el código con E/S en vivo
        self.session = InteractiveSession(self)
        self.session.output.connect(self.console.stream_out)
        self.session.errored.connect(self.console.stream_err)
        self.session.done.connect(self._on_run_finished)

        # botones de acción
        buttons = QHBoxLayout()
        self.btn_run = QPushButton(self.i18n.t("btn_run"))
        self.btn_check = QPushButton(self.i18n.t("btn_check"))
        self.btn_check.setObjectName("primary")
        self.btn_hint = QPushButton(self.i18n.t("btn_hint"))
        self.btn_solution = QPushButton(self.i18n.t("btn_solution"))
        self.btn_reset = QPushButton(self.i18n.t("btn_reset"))
        self.btn_run.clicked.connect(self.on_run)
        self.btn_check.clicked.connect(self.on_check)
        self.btn_hint.clicked.connect(self.on_hint)
        self.btn_solution.clicked.connect(self.on_solution)
        self.btn_reset.clicked.connect(self.on_reset)
        for b in (self.btn_run, self.btn_check, self.btn_hint, self.btn_solution, self.btn_reset):
            buttons.addWidget(b)
        buttons.addStretch(1)
        root.addLayout(buttons)
        self.btn_run.setToolTip("Ctrl+R")
        self.btn_check.setToolTip("Ctrl+Intro / Ctrl+Enter")

        # atajos de teclado / keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.on_check)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self.on_check)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.on_run)

    # ------------------------------------------------------------------ #
    @property
    def lang(self) -> str:
        return self.i18n.lang

    def set_lesson(self, lesson, lang: str) -> None:
        self.stash_draft()
        self.lesson = lesson
        self.exercises = list(lesson.exercises)
        self.idx = 0
        self._load_exercise()

    # --- borradores: el código a medias no se pierde al cambiar de ejercicio --- #
    def stash_draft(self) -> None:
        """Guarda como borrador el código del editor (si no es el inicial ni el ya resuelto)."""
        ex = self._current()
        if ex is None:
            return
        code = self.editor.toPlainText()
        solved = self.progress.get("solved_code", {}).get(ex.id)
        keep = code.strip() and code not in (ex.starter_code, solved)
        if prog.set_draft(self.progress, ex.id, code if keep else None):
            prog.save(self.progress)

    def discard_editor(self) -> None:
        """Olvida el código del editor sin guardarlo como borrador (reiniciar/importar)."""
        ex = self._current()
        self.editor.setPlainText(ex.starter_code if ex else "")

    def _current(self):
        if 0 <= self.idx < len(self.exercises):
            return self.exercises[self.idx]
        return None

    def _load_exercise(self) -> None:
        if hasattr(self, "session") and self.session.is_running():
            self.session.stop()
        self.console.clear_console()
        if hasattr(self, "input_line"):
            self.input_line.setEnabled(False)
        self.hint_idx = 0
        ex = self._current()
        self._refresh_buttons()

        if ex is None:
            self.lbl_counter.setText("")
            self.lbl_prompt.setText(
                f"<i>{'Esta lección es solo teórica.' if self.lang == 'es' else 'This lesson is theory-only.'}</i>"
            )
            self.editor.setPlainText("")
            return

        n = len(self.exercises)
        self.lbl_counter.setText(
            f"{self.i18n.t('exercise_n')} {self.idx + 1} {self.i18n.t('of')} {n}"
        )
        self.lbl_prompt.setText(_md_inline(ex.prompt_text(self.lang)))
        # prioridad: borrador (lo último que escribió) > código que ya pasó > inicial
        draft = prog.get_draft(self.progress, ex.id)
        saved = self.progress.get("solved_code", {}).get(ex.id)
        self.editor.setPlainText(draft or saved or ex.starter_code)
        if prog.is_exercise_completed(self.progress, ex.id):
            self.console.write_ok(self.i18n.t("exercise_done"))
        if draft:
            self.console.write_dim(self.i18n.t("draft_restored"))

    def _go(self, delta: int) -> None:
        self.goto_exercise(self.idx + delta)

    def goto_exercise(self, idx: int) -> None:
        if 0 <= idx < len(self.exercises):
            self.stash_draft()
            self.idx = idx
            self._load_exercise()

    # ------------------------------------------------------------------ #
    def _refresh_buttons(self) -> None:
        """Habilita los botones según haya ejercicio y si algo está en marcha.

        Mientras se comprueba (``_busy``) o corre el modo interactivo no se puede
        cambiar de ejercicio ni lanzar otra comprobación.
        """
        has = self._current() is not None
        running = self.session.is_running()
        idle = not (self._busy or running)
        self.btn_run.setEnabled(has and not self._busy)  # en marcha hace de "Detener"
        for b in (self.btn_check, self.btn_hint, self.btn_solution, self.btn_reset):
            b.setEnabled(has and idle)
        self.btn_prev.setEnabled(idle and self.idx > 0)
        self.btn_next.setEnabled(idle and self.idx < len(self.exercises) - 1)

    def _set_busy(self, busy: bool, label_key: str = "") -> None:
        self._busy = busy
        self._refresh_buttons()
        if busy and label_key:
            self.console.write_dim(self.i18n.t(label_key))

    def on_run(self) -> None:
        # Si ya hay un proceso interactivo en marcha, este botón lo detiene.
        if self.session.is_running():
            self.session.stop()
            return
        ex = self._current()
        # Los atajos (Ctrl+R) se disparan aunque el botón esté deshabilitado.
        if not ex or self._busy:
            return
        self.console.clear_console()
        self.editor.clear_error_line()
        self.session.start(self.editor.toPlainText())
        self._set_running_ui(True)
        self.input_line.setEnabled(True)
        self.input_line.setFocus()

    def _send_input(self) -> None:
        if self.session.is_running():
            text = self.input_line.text()
            self.session.send(text)
            self.console.stream_out(text + "\n")  # eco de lo que escribe el usuario
            self.input_line.remember(text)
            self.input_line.clear()

    def _on_run_finished(self, code: int) -> None:
        self.input_line.setEnabled(False)
        self.input_line.clear()
        self._set_running_ui(False)
        if code != 0 and self.session.err_buffer:
            exc = runner.parse_exception(self.session.err_buffer)
            if exc and exc.line:
                self.editor.set_error_line(exc.line)
        self.console.write_dim(f"[{self.i18n.t('process_ended')} · {code}]")

    def _set_running_ui(self, running: bool) -> None:
        self.btn_run.setText(self.i18n.t("btn_stop") if running else self.i18n.t("btn_run"))
        self._refresh_buttons()

    def on_check(self) -> None:
        ex = self._current()
        # Ctrl+Intro se dispara aunque el botón esté deshabilitado: sin esta
        # guarda se lanzaba un segundo hilo y el primero se destruía en marcha.
        if not ex or self._busy or self.session.is_running():
            return
        if self._worker is not None:
            self._worker.wait()  # el anterior ya avisó de que acabó; espera a que salga del todo
        self.console.clear_console()
        self.editor.clear_error_line()
        self._set_busy(True, "checking")
        exercise = {"tests": ex.tests}
        self._worker = RunnerWorker("check", self.editor.toPlainText(), exercise, ex.id)
        self._worker.finished_check.connect(self._show_check)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.start()

    def shutdown(self) -> None:
        """Detiene la ejecución interactiva y espera a la comprobación en curso.

        Se llama al cerrar la ventana: destruir un QThread que sigue corriendo
        cierra la aplicación de golpe.
        """
        self.session.stop()
        if self._worker is not None:
            self._worker.wait()

    # ------------------------------------------------------------------ #
    def _show_run(self, rr) -> None:
        if rr.stdout:
            self.console.write_stdout(rr.stdout)
        if rr.timed_out:
            self.console.write_error(self.i18n.t("timed_out"))
        elif rr.exception is not None:
            self.console.write_error(rr.exception.explanation(self.lang))
            self.editor.set_error_line(rr.exception.line)
            if rr.stderr:
                self.console.write_dim(rr.stderr.strip())
        elif not rr.stdout:
            self.console.write_dim("[exit 0]")

    def _show_check(self, ev, exercise_id: str, source: str) -> None:
        cur = self._current()
        if cur is None or cur.id != exercise_id:
            # El usuario cambió de lección mientras se comprobaba: se registra el
            # resultado en el ejercicio que de verdad se comprobó, pero no se
            # pinta en la consola, que ya muestra otro ejercicio.
            if ev.all_tests_passed:
                self.exerciseSolved.emit(exercise_id, source)
            elif ev.tests:
                self.exerciseFailed.emit(exercise_id)
            return

        # 1) sintaxis
        if ev.has_syntax_error:
            for issue in ev.static_issues:
                if issue.code == "syntax":
                    self.console.write_error("✗ " + issue.message(self.lang))
                    self.editor.set_error_line(issue.line)
            self.console.write_warn(self.i18n.t("syntax_blocked"))
            return

        # 2) avisos del analizador estático
        warnings = [i for i in ev.static_issues if i.severity != "error"]
        errors = [i for i in ev.static_issues if i.severity == "error"]
        if errors or warnings:
            self.console.write_dim(self.i18n.t("static_warnings"))
            for i in errors:
                self.console.write_error("  ✗ " + i.message(self.lang))
            for i in warnings:
                self.console.write_warn("  ! " + i.message(self.lang))

        # 3) ejercicios sin tests: solo ejecutamos
        if ev.run is not None and not ev.tests:
            self._show_run(ev.run)
            return

        # 4) resultados de los tests
        for t in ev.tests:
            if t.passed:
                self.console.write_ok(f"✓ {t.name}")
            else:
                self.console.write_error(f"✗ {t.name}")
                msg = t.message(self.lang)
                if msg:
                    self.console.write_dim("   " + msg.replace("\n", "\n   "))

        if ev.all_tests_passed:
            self.console.write_ok("─" * 28)
            self.console.write_ok(self.i18n.t("all_passed"))
            # el código que pasó los tests, no lo que haya ahora en el editor
            self.exerciseSolved.emit(exercise_id, source)
        else:
            self.console.write_warn(self.i18n.t("some_failed"))
            self.exerciseFailed.emit(exercise_id)

    # ------------------------------------------------------------------ #
    def on_hint(self) -> None:
        ex = self._current()
        if not ex:
            return
        hints = ex.hint_list(self.lang)
        if not hints:
            self.console.write_dim("—")
            return
        if self.hint_idx < len(hints):
            etiqueta = self.i18n.t("hint_n")
            self.console.write_info(f"» {etiqueta} {self.hint_idx + 1}/{len(hints)}: {hints[self.hint_idx]}")
            self.hint_idx += 1
            if self.hint_idx == len(hints):
                self.console.write_dim(self.i18n.t("hint_last"))
        else:
            self.console.write_dim(self.i18n.t("hint_no_more"))

    def on_solution(self) -> None:
        ex = self._current()
        if not ex:
            return
        # si aún no está resuelto, avisa de que ya no dará XP
        key = ("confirm_solution" if prog.is_exercise_completed(self.progress, ex.id)
               else "confirm_solution_xp")
        if QMessageBox.question(self, "PyQuest", self.i18n.t(key)) == QMessageBox.Yes:
            self.show_solution()

    def show_solution(self) -> None:
        ex = self._current()
        if not ex:
            return
        prog.mark_solution_viewed(self.progress, ex.id)
        prog.save(self.progress)
        self.editor.setPlainText(ex.solution)

    def on_reset(self) -> None:
        ex = self._current()
        if ex:
            self.editor.setPlainText(ex.starter_code)
            self.console.clear_console()
            if prog.set_draft(self.progress, ex.id, None):
                prog.save(self.progress)

    # ------------------------------------------------------------------ #
    def retranslate(self) -> None:
        if not self.session.is_running():
            self.btn_run.setText(self.i18n.t("btn_run"))
        self.input_line.setPlaceholderText(self.i18n.t("input_placeholder"))
        self.btn_check.setText(self.i18n.t("btn_check"))
        self.btn_hint.setText(self.i18n.t("btn_hint"))
        self.btn_solution.setText(self.i18n.t("btn_solution"))
        self.btn_reset.setText(self.i18n.t("btn_reset"))
        # recargar enunciado/contador en el nuevo idioma conservando el código
        ex = self._current()
        if ex:
            code = self.editor.toPlainText()
            n = len(self.exercises)
            self.lbl_counter.setText(
                f"{self.i18n.t('exercise_n')} {self.idx + 1} {self.i18n.t('of')} {n}"
            )
            self.lbl_prompt.setText(_md_inline(ex.prompt_text(self.lang)))
            self.editor.setPlainText(code)

    def refresh_theme(self) -> None:
        """Aplica los colores del tema nuevo al editor (resaltado de sintaxis)."""
        self.editor.rebuild_highlighter()

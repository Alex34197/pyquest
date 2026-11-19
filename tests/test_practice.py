"""
test_practice.py — comprobación de ejercicios en la GUI (offscreen).
test_practice.py — exercise checking in the GUI (offscreen).

Usa un progreso en memoria / un fichero temporal: nunca toca el progreso real.
"""
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def app(qapp):  # QApplication de sesión (conftest.py)
    return qapp


@pytest.fixture(scope="module")
def lesson():
    from pyquest import content
    course = content.load_course()
    # una lección corta con al menos 2 ejercicios
    return next(ls for _m, ls in course.all_lessons() if len(ls.exercises) >= 2)


def _practice(app):
    from pyquest.i18n import I18N
    from pyquest.widgets.practice_view import PracticeView
    return PracticeView(I18N("es"), {"solved_code": {}, "completed_exercises": []})


def _finish(pv, app):
    """Espera a que acabe la comprobación y entrega sus señales."""
    pv._worker.wait()
    app.processEvents()
    app.processEvents()


def test_second_check_ignored_while_busy(app, lesson):
    pv = _practice(app)
    pv.set_lesson(lesson, "es")
    pv.on_check()
    first = pv._worker
    assert pv._busy
    pv.on_check()      # p. ej. Ctrl+Intro pulsado dos veces
    pv.on_run()        # Ctrl+R durante la comprobación
    assert pv._worker is first
    assert not pv.session.is_running()
    _finish(pv, app)
    assert not pv._busy


def test_navigation_disabled_while_checking(app, lesson):
    pv = _practice(app)
    pv.set_lesson(lesson, "es")
    assert pv.btn_next.isEnabled()
    pv.on_check()
    assert not pv.btn_next.isEnabled()
    assert not pv.btn_check.isEnabled()
    _finish(pv, app)
    assert pv.btn_next.isEnabled()
    assert pv.btn_check.isEnabled()


def test_stale_result_credits_the_checked_exercise(app, lesson):
    pv = _practice(app)
    pv.set_lesson(lesson, "es")
    ex0, ex1 = lesson.exercises[0], lesson.exercises[1]
    pv.editor.setPlainText(ex0.solution)
    solved = []
    pv.exerciseSolved.connect(lambda eid, code: solved.append((eid, code)))
    pv.on_check()
    pv.goto_exercise(1)   # cambio de ejercicio (p. ej. Ctrl+J) antes del resultado
    _finish(pv, app)
    assert solved == [(ex0.id, ex0.solution)]
    assert pv._current().id == ex1.id


def test_app_completes_lesson_of_solved_exercise(app, tmp_path, monkeypatch):
    from pyquest import progress as prog
    monkeypatch.setattr(prog, "_path", lambda: tmp_path / "progress.json")
    from pyquest.app import MainWindow
    w = MainWindow()
    target = next(ls for _m, ls in w.course.all_lessons() if ls.exercises)
    w.open_lesson(len(w.course.modules) - 1, 0)   # abierta otra lección distinta
    assert w._lesson_at(*w.current) is not target
    for ex in target.exercises:
        w.on_exercise_solved(ex.id, ex.solution)
    assert prog.is_lesson_completed(w.progress, target.id)
    w.close()


# --- borradores, XP sin solución, importar progreso, examen, consola ---
def test_draft_survives_switching_exercises(app, lesson):
    pv = _practice(app)
    pv.set_lesson(lesson, "es")
    pv.editor.setPlainText("# a medias\nx = 1")
    pv.goto_exercise(1)
    assert pv.progress["drafts"][lesson.exercises[0].id] == "# a medias\nx = 1"
    pv.goto_exercise(0)
    assert pv.editor.toPlainText() == "# a medias\nx = 1"
    pv.on_reset()  # reiniciar descarta el borrador
    assert lesson.exercises[0].id not in pv.progress["drafts"]
    assert pv.editor.toPlainText() == lesson.exercises[0].starter_code


def test_unchanged_code_is_not_a_draft(app, lesson):
    pv = _practice(app)
    pv.set_lesson(lesson, "es")
    pv.goto_exercise(1)
    assert pv.progress.get("drafts", {}) == {}


def _window():
    from pyquest.app import MainWindow
    return MainWindow()


def test_no_xp_after_viewing_solution(app):
    w = _window()
    w.goto_next_pending()
    pv = w.lesson_view.practice
    ex = pv._current()
    pv.show_solution()
    w.on_exercise_solved(ex.id, ex.solution)
    assert w.progress["xp"] == 0
    assert ex.id in w.progress["completed_exercises"]
    ex2 = next(e for _m, ls in w.course.all_lessons() for e in ls.exercises
               if e.id not in w.progress["completed_exercises"])
    w.on_exercise_solved(ex2.id, ex2.solution)
    assert w.progress["xp"] == 10
    w.close()


def test_import_progress_applies_language_theme_and_font(app, tmp_path):
    import json
    w = _window()
    assert w.i18n.lang == "es"
    f = tmp_path / "importado.json"
    f.write_text(json.dumps({"language": "en", "theme": "amber", "font_pt": 15, "xp": 40,
                             "scanlines": False, "completed_exercises": ["m01l1e1"]}),
                 encoding="utf-8")
    assert w.load_progress_file(str(f))
    assert w.i18n.lang == "en"
    assert w.menu_file.title() == "File" and w.act_import.text() == "Import progress…"
    assert w.act_en.isChecked()
    assert w.theme_actions["amber"].isChecked()
    assert not w.act_scan.isChecked()
    assert w.content_pt == 15
    assert w.progress["xp"] == 40
    assert w.lesson_view.practice.btn_check.text() == "✓ Check"
    w.close()


def test_import_rejects_invalid_files(app, tmp_path):
    w = _window()
    bad = tmp_path / "malo.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    assert not w.load_progress_file(str(bad))
    bad.write_text("{roto", encoding="utf-8")
    assert not w.load_progress_file(str(bad))
    assert not w.load_progress_file(str(tmp_path / "no_existe.json"))
    w.close()


def test_exam_shows_feedback_per_question(app):
    import random
    from PySide6.QtWidgets import QLabel
    from pyquest.i18n import I18N
    from pyquest.widgets.quiz import ExamDialog
    progress = {}
    d = ExamDialog(I18N("es"), progress, rng=random.Random(1))
    total = len(d.items)
    # todas bien salvo la primera (que se deja sin responder)
    for grupo, it in list(zip(d.grupos, d.items))[1:]:
        grupo.button(it["correcta"]).setChecked(True)
    d.corregir()
    assert d.cajas[0].title().startswith("✗")
    assert all(c.title().startswith("✓") for c in d.cajas[1:])
    notas = d.cajas[0].findChildren(QLabel, "exam_feedback")
    assert len(notas) == 1 and "sin responder" in notas[0].text()
    assert not any(b.isEnabled() for b in d.grupos[1].buttons())
    assert progress["exam_score"] == round((total - 1) * 100 / total)
    d._on_button()  # nuevo intento: se vuelve a barajar y se puede responder
    assert not d.corregido and d.grupos[0].checkedId() == -1
    assert all(b.isEnabled() for b in d.grupos[0].buttons())


def test_console_caps_huge_output(app):
    from pyquest.widgets.console import ConsoleOutput, MAX_CHARS, MAX_LINES
    c = ConsoleOutput()
    c.write_stdout("x" * (MAX_CHARS * 3))
    assert len(c.toPlainText()) < MAX_CHARS + 100
    c.clear_console()
    c.write_stdout("línea\n" * (MAX_LINES * 2))
    assert c.blockCount() <= MAX_LINES

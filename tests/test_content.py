"""Tests del contenido: esquema válido y cada solución pasa sus propios tests."""
from pyquest import content as C
from pyquest import runner as R


def test_schema_is_valid():
    course = C.load_course()
    problems = C.validate_course(course)
    assert problems == [], problems


def test_modules_loaded():
    course = C.load_course()
    assert len(course.modules) >= 3
    assert course.lesson_count() >= 9


def test_every_solution_passes_its_tests():
    course = C.load_course()
    for _module, lesson in course.all_lessons():
        for ex in lesson.exercises:
            ev = R.evaluate(ex.solution, {"tests": ex.tests})
            assert not ev.has_syntax_error, f"{ex.id}: error de sintaxis en la solución"
            assert ev.all_tests_passed, f"{ex.id}: la solución no pasa sus tests"


def test_starters_do_not_trivially_pass():
    course = C.load_course()
    for _module, lesson in course.all_lessons():
        for ex in lesson.exercises:
            ev = R.evaluate(ex.starter_code, {"tests": ex.tests})
            assert not (ev.all_tests_passed and not ev.has_syntax_error), \
                f"{ex.id}: el código inicial ya pasa los tests"

"""
test_extra.py — comprobaciones estructurales del curso.
test_extra.py — structural checks for the course.

Estos tests no ejecutan código del alumno (de eso se encarga test_content);
verifican que el contenido esté bien formado y sea bilingüe y consistente.
"""
from __future__ import annotations

import pytest

from pyquest import content

LANGS = ("es", "en")


@pytest.fixture(scope="module")
def course():
    return content.load_course()


def test_at_least_15_modules(course):
    assert len(course.modules) >= 15


def test_module_ids_unique(course):
    ids = [m.id for m in course.modules]
    assert len(ids) == len(set(ids)), "hay ids de módulo duplicados"


def test_lesson_ids_unique(course):
    ids = [ls.id for _m, ls in course.all_lessons()]
    assert len(ids) == len(set(ids)), "hay ids de lección duplicados"


def test_exercise_ids_unique(course):
    ids = [ex.id for _m, ls in course.all_lessons() for ex in ls.exercises]
    assert len(ids) == len(set(ids)), "hay ids de ejercicio duplicados"


def test_modules_have_bilingual_title(course):
    for m in course.modules:
        for lang in LANGS:
            assert m.title.get(lang), f"módulo {m.id} sin título en {lang}"


def test_lessons_have_bilingual_title_and_theory(course):
    for _m, ls in course.all_lessons():
        for lang in LANGS:
            assert ls.title.get(lang), f"lección {ls.id} sin título en {lang}"
            assert ls.theory.get(lang), f"lección {ls.id} sin teoría en {lang}"


def test_exercises_have_prompt_hints_and_tests(course):
    for _m, ls in course.all_lessons():
        for ex in ls.exercises:
            for lang in LANGS:
                assert ex.prompt.get(lang), f"{ex.id} sin enunciado en {lang}"
                assert ex.hints.get(lang), f"{ex.id} sin pistas en {lang}"
            assert ex.tests, f"{ex.id} no tiene tests"
            assert ex.solution.strip(), f"{ex.id} no tiene solución"


def test_min_content_volume(course):
    n_ex = sum(len(ls.exercises) for _m, ls in course.all_lessons())
    n_les = sum(1 for _ in course.all_lessons())
    assert n_les >= 30, f"esperaba >=30 lecciones, hay {n_les}"
    assert n_ex >= 60, f"esperaba >=60 ejercicios, hay {n_ex}"

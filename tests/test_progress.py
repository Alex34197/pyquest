"""Tests del progreso (sin Qt): normalización, carga robusta, reinicio, borradores.

El fichero de progreso apunta a una carpeta temporal (ver conftest.py).
"""
import json

from pyquest import progress as P


def test_normalize_rejects_wrong_types_and_fixes_values():
    data = P.normalize({
        "xp": "mucho", "streak": -3, "language": "fr", "theme": "rosa", "font_pt": 99,
        "scanlines": "si", "completed_exercises": ["a", "a", 3, "b"], "fails": {"a": 2, "b": "x"},
        "solved_code": {"a": "print(1)", "b": 5}, "last_lesson": [1], "window": [800, 600],
        "futuro": {"clave": 1},
    })
    assert data["xp"] == 0 and data["streak"] == 0
    assert data["language"] == "es" and data["theme"] == "green"
    assert data["font_pt"] == 24
    assert data["scanlines"] is True
    assert data["completed_exercises"] == ["a", "b"]
    assert data["fails"] == {"a": 2}
    assert data["solved_code"] == {"a": "print(1)"}
    assert data["last_lesson"] == [0, 0]
    assert data["window"] == [800, 600]
    assert data["futuro"] == {"clave": 1}  # claves desconocidas se conservan


def test_normalize_does_not_share_mutable_defaults():
    a = P.normalize({})
    a["bookmarks"].append("x")
    a["drafts"]["e"] = "code"
    b = P.normalize({})
    assert b["bookmarks"] == [] and b["drafts"] == {}


def test_load_moves_corrupt_file_aside(tmp_path):
    p = P._path()
    p.write_text("{esto no es json", encoding="utf-8")
    data = P.load()
    assert data["xp"] == 0
    assert (p.parent / "progress.corrupt.json").exists()


def test_save_and_load_roundtrip():
    data = P.normalize({"xp": 30, "language": "en"})
    P.save(data)
    again = P.load()
    assert again["xp"] == 30 and again["language"] == "en"
    assert json.loads(P._path().read_text(encoding="utf-8"))["xp"] == 30


def test_reset_keeps_preferences_and_bookmarks():
    data = P.normalize({"xp": 50, "theme": "amber", "language": "en", "bookmarks": ["l1"],
                        "completed_exercises": ["e1"], "drafts": {"e2": "x"}, "exam_passed": True})
    ref = data
    P.reset(data)
    assert data is ref  # en sitio
    assert data["xp"] == 0 and data["completed_exercises"] == [] and data["drafts"] == {}
    assert data["exam_passed"] is False
    assert data["theme"] == "amber" and data["language"] == "en" and data["bookmarks"] == ["l1"]


def test_drafts_and_solution_viewed():
    data = P.normalize({})
    assert P.set_draft(data, "e1", "x = 1")
    assert not P.set_draft(data, "e1", "x = 1")  # sin cambios
    assert P.get_draft(data, "e1") == "x = 1"
    P.mark_solution_viewed(data, "e1")
    assert P.solution_was_viewed(data, "e1")
    P.mark_exercise_completed(data, "e1", "x = 2")
    assert P.get_draft(data, "e1") is None  # al resolverlo el borrador sobra
    P.mark_solution_viewed(data, "e9")
    P.mark_exercise_completed(data, "e8", "ok")
    P.mark_solution_viewed(data, "e8")  # ya resuelto: verla después no cuenta
    assert not P.solution_was_viewed(data, "e8")

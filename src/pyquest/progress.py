"""
progress.py — persistencia del progreso del usuario.
progress.py — user progress persistence.

Guarda en un único JSON dentro del directorio de datos del usuario qué
lecciones y ejercicios se han completado, además de preferencias (idioma,
scanlines). No depende de Qt para poder probarse de forma aislada.
"""
from __future__ import annotations

import copy
import datetime
import json
from typing import Any

from .util import user_data_dir

_PROGRESS_FILE = "progress.json"
_LANGUAGES = ("es", "en")
_THEMES = ("green", "amber", "dos", "light")  # mismos nombres que theme.py
_FONT_RANGE = (8, 24)

_DEFAULT: dict[str, Any] = {
    "version": 1,
    "language": "es",
    "scanlines": True,
    "theme": "green",
    "font_pt": 11,
    "completed_lessons": [],     # ids de lección
    "completed_exercises": [],   # ids de ejercicio
    "solved_code": {},           # exercise_id -> último código que pasó los tests
    "xp": 0,                     # puntos de experiencia
    "streak": 0,                 # racha de días seguidos practicando
    "last_active": "",           # último día con actividad (ISO)
    "achievements": [],          # ids de logros desbloqueados
    "last_lesson": [0, 0],        # último (módulo, lección) abierto
    "window": [1180, 760],        # tamaño de ventana recordado
    "fails": {},                  # exercise_id -> nº de intentos fallidos
    "bookmarks": [],              # ids de lección marcados
    "exam_passed": False,         # examen final aprobado
    "exam_score": 0,              # última puntuación del examen (%)
    "drafts": {},                 # exercise_id -> código a medias (aún sin pasar los tests)
    "solution_viewed": [],        # ids de ejercicio cuya solución se vio antes de resolverlo
}


def _path():
    return user_data_dir() / _PROGRESS_FILE


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _int_pair(v) -> bool:
    return isinstance(v, list) and len(v) == 2 and all(_is_int(x) and x >= 0 for x in v)


def normalize(stored: Any) -> dict[str, Any]:
    """Convierte cualquier cosa leída de disco en un progreso válido.

    Parte de una copia PROFUNDA de los valores por defecto y solo acepta los
    campos del tipo correcto, así un fichero antiguo, editado a mano o
    importado de otra versión no puede romper la app. Las claves desconocidas
    se conservan (compatibilidad con versiones futuras).
    """
    data = copy.deepcopy(_DEFAULT)
    if not isinstance(stored, dict):
        return data
    for key, val in stored.items():
        if key not in _DEFAULT:
            data[key] = val
            continue
        default = _DEFAULT[key]
        if isinstance(default, bool):
            ok = isinstance(val, bool)
        elif isinstance(default, int):
            ok = _is_int(val) and val >= 0
        else:
            ok = isinstance(val, type(default))
        if ok:
            data[key] = val

    for key in ("completed_lessons", "completed_exercises", "achievements",
                "bookmarks", "solution_viewed"):
        data[key] = list(dict.fromkeys(x for x in data[key] if isinstance(x, str)))
    for key in ("solved_code", "drafts"):
        data[key] = {k: v for k, v in data[key].items() if isinstance(k, str) and isinstance(v, str)}
    data["fails"] = {k: v for k, v in data["fails"].items() if isinstance(k, str) and _is_int(v) and v > 0}

    if data["language"] not in _LANGUAGES:
        data["language"] = _DEFAULT["language"]
    if data["theme"] not in _THEMES:
        data["theme"] = _DEFAULT["theme"]
    data["font_pt"] = min(_FONT_RANGE[1], max(_FONT_RANGE[0], data["font_pt"]))
    data["exam_score"] = min(100, data["exam_score"])
    if not _int_pair(data["last_lesson"]):
        data["last_lesson"] = list(_DEFAULT["last_lesson"])
    if not _int_pair(data["window"]):
        data["window"] = list(_DEFAULT["window"])
    return data


def load() -> dict[str, Any]:
    """Carga el progreso; si no existe o está corrupto devuelve los valores por defecto.

    Un fichero ilegible no se pierde: se aparta como ``progress.corrupt.json``
    antes de que el primer guardado lo sobrescriba.
    """
    p = _path()
    stored: Any = {}
    if p.exists():
        try:
            stored = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):  # JSONDecodeError y UnicodeDecodeError son ValueError
            try:
                p.replace(p.with_name("progress.corrupt.json"))
            except OSError:
                pass
    return normalize(stored)


def save(data: dict[str, Any]) -> None:
    """Guarda el progreso de forma atómica."""
    p = _path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def mark_lesson_completed(data: dict[str, Any], lesson_id: str) -> None:
    if lesson_id not in data["completed_lessons"]:
        data["completed_lessons"].append(lesson_id)


def mark_exercise_completed(data: dict[str, Any], exercise_id: str, code: str = "") -> None:
    if exercise_id not in data["completed_exercises"]:
        data["completed_exercises"].append(exercise_id)
    if code:
        data["solved_code"][exercise_id] = code
    data.setdefault("drafts", {}).pop(exercise_id, None)  # el borrador ya no hace falta


def mark_solution_viewed(data: dict[str, Any], exercise_id: str) -> None:
    """Apunta que se vio la solución ANTES de resolver el ejercicio (resolverlo no dará XP)."""
    if is_exercise_completed(data, exercise_id):
        return
    viewed = data.setdefault("solution_viewed", [])
    if exercise_id not in viewed:
        viewed.append(exercise_id)


def solution_was_viewed(data: dict[str, Any], exercise_id: str) -> bool:
    return exercise_id in data.get("solution_viewed", [])


def set_draft(data: dict[str, Any], exercise_id: str, code: str | None) -> bool:
    """Guarda (o borra, con ``None``) el borrador de un ejercicio. Devuelve True si cambió."""
    drafts = data.setdefault("drafts", {})
    if code is None:
        return drafts.pop(exercise_id, None) is not None
    if drafts.get(exercise_id) == code:
        return False
    drafts[exercise_id] = code
    return True


def get_draft(data: dict[str, Any], exercise_id: str) -> str | None:
    return data.get("drafts", {}).get(exercise_id)


def reset(data: dict[str, Any]) -> None:
    """Borra el progreso EN SITIO (la vista comparte la referencia) conservando
    preferencias (idioma, tema, fuente, ventana...) y marcadores."""
    keep = {k: data[k] for k in ("language", "scanlines", "theme", "font_pt", "window", "bookmarks")
            if k in data}
    data.clear()
    data.update(copy.deepcopy(_DEFAULT))
    data.update(keep)


def is_lesson_completed(data: dict[str, Any], lesson_id: str) -> bool:
    return lesson_id in data.get("completed_lessons", [])


def is_exercise_completed(data: dict[str, Any], exercise_id: str) -> bool:
    return exercise_id in data.get("completed_exercises", [])


# --------------------------------------------------------------------------- #
# Gamificación: XP, racha y logros
# --------------------------------------------------------------------------- #
XP_PER_EXERCISE = 10


def register_activity(data: dict[str, Any]) -> None:
    """Actualiza la racha de días seguidos según la fecha de hoy."""
    today = datetime.date.today()
    last_s = data.get("last_active", "")
    if last_s == today.isoformat():
        return
    streak = data.get("streak", 0)
    if last_s:
        try:
            gap = (today - datetime.date.fromisoformat(last_s)).days
        except ValueError:
            gap = 99
        streak = streak + 1 if gap == 1 else 1
    else:
        streak = 1
    data["streak"] = streak
    data["last_active"] = today.isoformat()


_ACHIEVEMENT_NAMES = {
    "primer_paso": {"es": "Primer paso", "en": "First step"},
    "aprendiz":    {"es": "Aprendiz", "en": "Apprentice"},
    "constante":   {"es": "Constante", "en": "Consistent"},
    "maestria":    {"es": "Maestría", "en": "Mastery"},
    "racha_3":     {"es": "Racha de 3 días", "en": "3-day streak"},
    "racha_7":     {"es": "Racha de 7 días", "en": "7-day streak"},
}
_ACHIEVEMENT_ORDER = ["primer_paso", "aprendiz", "constante", "maestria", "racha_3", "racha_7"]


def check_new_achievements(data: dict[str, Any], exercises_done: int,
                           total_exercises: int = 0) -> list[dict]:
    """Desbloquea logros según ejercicios resueltos y racha. Devuelve los nombres nuevos.

    ``total_exercises`` permite que "Maestría" se ajuste al número real de
    ejercicios del curso (se completa al resolverlos todos).
    """
    streak = data.get("streak", 0)
    met = {
        "primer_paso": exercises_done >= 1,
        "aprendiz":    exercises_done >= 10,
        "constante":   exercises_done >= 25,
        "maestria":    total_exercises > 0 and exercises_done >= total_exercises,
        "racha_3":     streak >= 3,
        "racha_7":     streak >= 7,
    }
    have = set(data.get("achievements", []))
    nuevos = []
    for aid in _ACHIEVEMENT_ORDER:
        if met.get(aid) and aid not in have:
            data.setdefault("achievements", []).append(aid)
            nuevos.append(_ACHIEVEMENT_NAMES[aid])
    return nuevos


def all_achievements() -> list[tuple]:
    """Devuelve todos los logros en orden: lista de (id, {es, en})."""
    return [(aid, _ACHIEVEMENT_NAMES[aid]) for aid in _ACHIEVEMENT_ORDER]


def record_fail(data: dict[str, Any], exercise_id: str) -> None:
    """Suma un intento fallido al ejercicio."""
    fails = data.setdefault("fails", {})
    fails[exercise_id] = fails.get(exercise_id, 0) + 1


def fail_count(data: dict[str, Any], exercise_id: str) -> int:
    return data.get("fails", {}).get(exercise_id, 0)


def toggle_bookmark(data: dict[str, Any], lesson_id: str) -> bool:
    """Marca/desmarca una lección. Devuelve True si quedó marcada."""
    bm = data.setdefault("bookmarks", [])
    if lesson_id in bm:
        bm.remove(lesson_id)
        return False
    bm.append(lesson_id)
    return True


def is_bookmarked(data: dict[str, Any], lesson_id: str) -> bool:
    return lesson_id in data.get("bookmarks", [])

"""
content.py — carga y valida el contenido didáctico (módulos/lecciones).
content.py — loads and validates the learning content (modules/lessons).

Formato (todo en JSON, bilingüe ES/EN):

  content/
    modules.json                      -> {"modules": ["module_01_...", ...]}
    module_01_xxx/
      module.json                     -> metadatos + lista de lecciones
      lesson_01.json                  -> teoría + ejercicios
      ...

Los textos largos (código, salidas) se guardan como LISTAS de líneas y se
unen con '\n' al cargar, para que el JSON sea legible y sin '\n' incrustados.

Bloques de teoría admitidos (campo "type"):
  heading | text | code | output | note
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .util import content_dir

VALID_BLOCK_TYPES = {"heading", "text", "code", "output", "note"}


def _join(value) -> str:
    """Une una lista de líneas; deja las cadenas tal cual."""
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value)


def _loc(d: dict, lang: str, fallback: str = "es") -> str:
    if not isinstance(d, dict):
        return str(d)
    return d.get(lang) or d.get(fallback) or next(iter(d.values()), "")


# --------------------------------------------------------------------------- #
# Modelo de datos
# --------------------------------------------------------------------------- #
@dataclass
class Exercise:
    id: str
    prompt: dict           # {"es": "...", "en": "..."}
    starter_code: str
    solution: str
    hints: dict            # {"es": [...], "en": [...]}
    tests: list

    def prompt_text(self, lang): return _loc(self.prompt, lang)
    def hint_list(self, lang): return self.hints.get(lang) or self.hints.get("es") or []


@dataclass
class Lesson:
    id: str
    title: dict
    theory: dict           # {"es": [blocks], "en": [blocks]}
    exercises: list[Exercise] = field(default_factory=list)

    def title_text(self, lang): return _loc(self.title, lang)
    def theory_blocks(self, lang): return self.theory.get(lang) or self.theory.get("es") or []


@dataclass
class Module:
    id: str
    title: dict
    summary: dict
    lessons: list[Lesson] = field(default_factory=list)

    def title_text(self, lang): return _loc(self.title, lang)
    def summary_text(self, lang): return _loc(self.summary, lang)


@dataclass
class Course:
    modules: list[Module] = field(default_factory=list)

    def all_lessons(self):
        for m in self.modules:
            for ls in m.lessons:
                yield m, ls

    def lesson_count(self):
        return sum(len(m.lessons) for m in self.modules)


# --------------------------------------------------------------------------- #
# Carga
# --------------------------------------------------------------------------- #
def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_exercise(d: dict) -> Exercise:
    return Exercise(
        id=d["id"],
        prompt=d.get("prompt", {}),
        starter_code=_join(d.get("starter_code", "")),
        solution=_join(d.get("solution", "")),
        hints=d.get("hints", {}),
        tests=d.get("tests", []),
    )


def _parse_lesson(d: dict) -> Lesson:
    return Lesson(
        id=d["id"],
        title=d.get("title", {}),
        theory=d.get("theory", {"es": [], "en": []}),
        exercises=[_parse_exercise(e) for e in d.get("exercises", [])],
    )


def load_course(root: Path | None = None) -> Course:
    """Carga el curso completo desde la carpeta de contenido."""
    root = Path(root) if root else content_dir()
    index = _read_json(root / "modules.json")
    course = Course()
    for mod_dir_name in index.get("modules", []):
        mod_dir = root / mod_dir_name
        meta = _read_json(mod_dir / "module.json")
        module = Module(
            id=meta["id"],
            title=meta.get("title", {}),
            summary=meta.get("summary", {}),
        )
        for lesson_file in meta.get("lessons", []):
            module.lessons.append(_parse_lesson(_read_json(mod_dir / lesson_file)))
        course.modules.append(module)
    return course


# --------------------------------------------------------------------------- #
# Validación (se usa en los tests y al arrancar la app)
# --------------------------------------------------------------------------- #
def validate_course(course: Course) -> list[str]:
    """Devuelve una lista de problemas encontrados (vacía si todo está bien)."""
    problems: list[str] = []
    seen_ids: set[str] = set()

    def check_loc(field_name, d, where):
        for lang in ("es", "en"):
            if not _loc(d, lang):
                problems.append(f"{where}: falta texto '{field_name}' en '{lang}'.")

    if not course.modules:
        problems.append("El curso no tiene módulos.")

    for m in course.modules:
        check_loc("title", m.title, f"módulo {m.id}")
        if not m.lessons:
            problems.append(f"módulo {m.id}: sin lecciones.")
        for ls in m.lessons:
            if ls.id in seen_ids:
                problems.append(f"id de lección duplicado: {ls.id}")
            seen_ids.add(ls.id)
            check_loc("title", ls.title, f"lección {ls.id}")
            for lang in ("es", "en"):
                blocks = ls.theory_blocks(lang)
                if not blocks:
                    problems.append(f"lección {ls.id}: teoría vacía en '{lang}'.")
                for b in blocks:
                    if b.get("type") not in VALID_BLOCK_TYPES:
                        problems.append(f"lección {ls.id}: bloque con tipo inválido '{b.get('type')}'.")
            for ex in ls.exercises:
                if ex.id in seen_ids:
                    problems.append(f"id de ejercicio duplicado: {ex.id}")
                seen_ids.add(ex.id)
                check_loc("prompt", ex.prompt, f"ejercicio {ex.id}")
                if not ex.tests:
                    problems.append(f"ejercicio {ex.id}: sin tests.")
                for t in ex.tests:
                    ttype = t.get("type", "code")
                    if ttype == "function" and "function" not in t:
                        problems.append(f"ejercicio {ex.id}: test 'function' sin clave 'function'.")
                    if ttype == "code" and "harness" not in t:
                        problems.append(f"ejercicio {ex.id}: test 'code' sin 'harness'.")
    return problems


def load_exam(root: Path | None = None) -> dict:
    """Carga el examen final (content/exam.json)."""
    root = Path(root) if root else content_dir()
    p = root / "exam.json"
    if not p.exists():
        return {"pass": 0.8, "questions": []}
    return _read_json(p)

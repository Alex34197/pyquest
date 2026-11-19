"""
util.py — utilidades de rutas (recursos empaquetados y directorios de usuario).
util.py — path helpers (bundled resources and per-user directories).

Estas funciones funcionan tanto en desarrollo (ejecutando desde el código
fuente) como dentro de un ejecutable generado con PyInstaller.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from . import __app_name__


def is_frozen() -> bool:
    """True si corremos dentro de un binario de PyInstaller."""
    return getattr(sys, "frozen", False)


def resource_path(*parts: str) -> Path:
    """
    Devuelve la ruta a un recurso de la raíz del proyecto (p. ej. ``assets``)
    tanto en desarrollo como empaquetado.

    - Empaquetado (PyInstaller): los datos viven junto al ejecutable / en
      ``sys._MEIPASS``.
    - Desarrollo: se resuelve relativo a la raíz del proyecto.
    """
    if is_frozen():
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        # .../src/pyquest/util.py  ->  raíz del proyecto = parents[2]
        base = Path(__file__).resolve().parents[2]
    return base.joinpath(*parts)


def content_dir() -> Path:
    """Carpeta raíz del contenido (módulos, lecciones, examen).

    Vive DENTRO del paquete (``pyquest/course``) para que viaje con él en los
    tres casos: desarrollo, ``pip install`` y PyInstaller (los ``.spec`` la
    copian a ``pyquest/course``, junto a los módulos congelados).
    """
    return Path(__file__).resolve().parent / "course"


def user_data_dir() -> Path:
    """
    Directorio por usuario donde se guarda el progreso, siguiendo las
    convenciones de cada sistema operativo.
    """
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        path = Path(base) / __app_name__
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / __app_name__
    else:  # Linux / *nix
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        path = Path(base) / __app_name__
    path.mkdir(parents=True, exist_ok=True)
    return path

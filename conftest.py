"""Hace importable el paquete pyquest (en src/) al ejecutar pytest.

Además, ningún test toca el progreso REAL del usuario: el fichero de progreso se
redirige a una carpeta temporal en cada test.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))


@pytest.fixture(autouse=True)
def _isolated_progress(tmp_path, monkeypatch):
    from pyquest import progress
    monkeypatch.setattr(progress, "_path", lambda: tmp_path / "progress.json")

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


@pytest.fixture(scope="session")
def qapp():
    """Una sola QApplication para toda la sesión de tests (GUI offscreen).

    Al terminar cierra y destruye todas las ventanas MIENTRAS la aplicación
    sigue viva: si Python destruye la QApplication antes que los widgets al
    salir, Qt revienta con un segfault (visto en Linux/macOS con Python 3.10).
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
    except Exception as e:  # libs gráficas ausentes / sin plataforma
        pytest.skip(f"Qt no disponible: {e}")
    yield app

    import gc

    from PySide6.QtCore import QCoreApplication, QEvent
    for w in app.topLevelWidgets():
        w.close()
        w.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()
    gc.collect()

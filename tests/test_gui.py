"""
test_gui.py — humo de la interfaz (offscreen). Se salta solo si Qt no arranca.
test_gui.py — GUI smoke test (offscreen). Self-skips if Qt can't start.
"""
import os
import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def app(qapp):  # QApplication de sesión (conftest.py)
    return qapp


def _make_window():
    try:
        from pyquest.app import MainWindow
        return MainWindow()
    except Exception as e:
        pytest.skip(f"GUI no arranca: {e}")


def test_boot_widgets(app):
    w = _make_window()
    assert len(w.course.modules) >= 1
    assert hasattr(w.sidebar, "bar")
    assert "light" in w.theme_actions


def test_playground_and_stats(app):
    w = _make_window()
    w.open_playground()
    assert w.playground is not None
    from pyquest.widgets.stats import StatsDialog
    d = StatsDialog(w.i18n, w.course, w.progress, w.content_pt, w)
    assert "%" in d.view.toPlainText()


def test_editor_helpers(app):
    _make_window()  # asegura QApplication
    from pyquest.widgets.code_editor import CodeEditor
    ed = CodeEditor()
    ed.setPlainText("a = 1\nb = 2")
    ed.selectAll()
    ed.toggle_comment()
    assert ed.toPlainText() == "# a = 1\n# b = 2"
    ed.selectAll()
    ed.toggle_comment()
    assert ed.toPlainText() == "a = 1\nb = 2"
    ed.selectAll()
    ed._shift_lines(dedent=False)
    assert ed.toPlainText() == "    a = 1\n    b = 2"

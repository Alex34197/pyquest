"""Tests del motor de ejecución y corrección (no necesitan Qt)."""
from pyquest import runner as R


def test_syntax_error_detected():
    issues = R.analyze_static("def f(:\n    pass")
    assert any(i.code == "syntax" for i in issues)


def test_run_hello():
    rr = R.run_code("print('hi')")
    assert rr.ok
    assert rr.stdout.strip() == "hi"


def test_runtime_exception_parsed():
    rr = R.run_code("print(1 / 0)")
    assert rr.exception is not None
    assert rr.exception.etype == "ZeroDivisionError"
    assert rr.exception.line == 1


def test_timeout():
    rr = R.run_code("while True:\n    pass", timeout=2.0)
    assert rr.timed_out


def test_stdout_test_pass_and_fail():
    ok = R.run_tests("print('ok')", [{"type": "stdout", "expected": "ok"}])
    assert ok[0].passed
    bad = R.run_tests("print('no')", [{"type": "stdout", "expected": "ok"}])
    assert not bad[0].passed


def test_function_test_pass_and_fail():
    t = [{"type": "function", "function": "f", "cases": [{"args": [3], "expected": 6}]}]
    assert R.run_tests("def f(n):\n    return n * 2", t)[0].passed
    assert not R.run_tests("def f(n):\n    return n + 2", t)[0].passed


def test_function_test_with_string_args():
    t = [{"type": "function", "function": "g",
          "cases": [{"args": ["hola"], "expected": 4}]}]
    assert R.run_tests("def g(s):\n    return len(s)", t)[0].passed


def test_code_harness():
    t = [{"type": "code", "harness": "assert suma(2, 3) == 5"}]
    assert R.run_tests("def suma(a, b):\n    return a + b", t)[0].passed


def test_evaluate_blocks_on_syntax_error():
    ev = R.evaluate("def f(:", {"tests": [{"type": "stdout", "expected": "x"}]})
    assert ev.has_syntax_error
    assert ev.tests == []


def test_temp_path_hidden_in_traceback():
    rr = R.run_code("raise ValueError('x')")
    # la ruta temporal del directorio no debe aparecer; sí el nombre del archivo
    assert "user_code.py" in rr.stderr
    assert "/tmp/" not in rr.stderr or "pyquest_" not in rr.stderr


# --- Sandbox: no debe romper la librería estándar (bug de asyncio en Windows) ---
def test_asyncio_works_in_sandbox():
    rr = R.run_code("import asyncio\nasync def d(x):\n    return x * 2\nprint(asyncio.run(d(5)))")
    assert rr.ok, rr.stderr
    assert rr.stdout.strip() == "10"


def test_sandbox_blocks_external_network_but_allows_loopback():
    rr = R.run_code("import socket\nsocket.socket().connect(('8.8.8.8', 53))")
    assert rr.exception is not None and rr.exception.etype == "PermissionError"
    rr = R.run_code("import socket\na, b = socket.socketpair()\na.send(b'hi')\nprint(b.recv(2))")
    assert rr.ok, rr.stderr
    assert rr.stdout.strip() == "b'hi'"


def test_sandbox_blocks_subprocess_but_popen_is_subclassable():
    rr = R.run_code("import subprocess\nsubprocess.run(['echo', 'x'])")
    assert rr.exception is not None and rr.exception.etype == "PermissionError"
    rr = R.run_code("import subprocess\nclass P(subprocess.Popen):\n    pass\nP(['echo', 'x'])")
    assert rr.exception is not None and rr.exception.etype == "PermissionError"
    assert rr.exception.line == 4


# --- La línea del error debe ser la del código del alumno ---
def test_error_line_ignores_stdlib_frames():
    tb = (
        "Traceback (most recent call last):\n"
        r'  File "C:\Temp\pyquest_run_x\user_code.py", line 2, in <module>' "\n"
        "    json.loads('{malo')\n"
        r'  File "C:\Python313\Lib\json\__init__.py", line 346, in loads' "\n"
        "    return _default_decoder.decode(s)\n"
        "json.decoder.JSONDecodeError: Expecting property name: line 1 column 2 (char 1)\n"
    )
    exc = R.parse_exception(tb)
    assert exc.etype == "JSONDecodeError"
    assert exc.line == 2


def test_error_line_none_when_no_user_frame():
    tb = ('Traceback (most recent call last):\n'
          '  File "/usr/lib/python3/x.py", line 133, in <module>\n'
          'TypeError: boom\n')
    assert R.parse_exception(tb).line is None


def test_syntax_error_traceback_hides_pyquest_internals():
    rr = R.run_code("x = 1\ny = (")
    assert rr.exception is not None and rr.exception.etype == "SyntaxError"
    assert rr.exception.line == 2
    assert "runner.py" not in rr.stderr


def test_user_annotations_are_real_types():
    # runner.py usa "from __future__ import annotations"; no debe contagiarse al alumno
    rr = R.run_code("def f(a: int) -> int:\n    return a\nprint(f.__annotations__['a'] is int)")
    assert rr.ok, rr.stderr
    assert rr.stdout.strip() == "True"


# --- Límites de recursos y más vías del sandbox ---
import sys  # noqa: E402

import pytest  # noqa: E402


@pytest.mark.skipif(sys.platform == "darwin", reason="macOS no aplica RLIMIT_AS")
def test_memory_limit_raises_memory_error():
    rr = R.run_code("x = bytearray(3 * 1024 ** 3)\nprint(len(x))")
    assert rr.exception is not None and rr.exception.etype == "MemoryError"
    assert "2 GB" in rr.exception.explanation_es


def test_moderate_memory_is_fine():
    rr = R.run_code("x = bytearray(300 * 1024 ** 2)\nprint(len(x))")
    assert rr.ok, rr.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="solo Windows")
def test_winapi_create_process_blocked():
    rr = R.run_code("import _winapi\n"
                    "_winapi.CreateProcess(None, 'cmd /c exit', None, None, False, 0, None, None, None)")
    assert rr.exception is not None and rr.exception.etype == "PermissionError"


def test_pathlib_cannot_write_outside_workdir():
    rr = R.run_code("import os\nfrom pathlib import Path\n"
                    "Path(os.getcwd() + '_vecina.txt').write_text('x')")
    assert rr.exception is not None and rr.exception.etype == "PermissionError"
    rr = R.run_code("from pathlib import Path\nPath('a.txt').write_text('hola')\n"
                    "print(Path('a.txt').read_text())")
    assert rr.ok and rr.stdout.strip() == "hola"


def test_tempfile_works_inside_workdir():
    rr = R.run_code("import tempfile\nwith tempfile.TemporaryFile() as f:\n"
                    "    f.write(b'x')\nprint('ok')")
    assert rr.ok, rr.stderr

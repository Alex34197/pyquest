"""
interactive.py — ejecución interactiva del código del usuario con QProcess.
interactive.py — interactive execution of user code via QProcess.

A diferencia del motor de corrección (que ejecuta en lote y compara con tests),
esto lanza el código como un proceso vivo: su salida aparece en streaming y se
le puede enviar texto por la entrada estándar, de modo que `input()` funciona
de verdad mientras el programa corre.
"""
from __future__ import annotations

import os
import shutil
import tempfile

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, Signal


class InteractiveSession(QObject):
    output = Signal(str)   # fragmento de stdout
    errored = Signal(str)  # fragmento de stderr
    done = Signal(int)     # código de salida

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc: QProcess | None = None
        self._tmpdir: str | None = None
        self.err_buffer = ""

    # ------------------------------------------------------------------ #
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.state() != QProcess.NotRunning

    def start(self, source: str) -> None:
        """Lanza el código fuente como proceso interactivo."""
        from .. import runner  # evita import circular en carga

        self.stop()
        self.err_buffer = ""
        self._tmpdir = tempfile.mkdtemp(prefix="pyquest_run_")
        script = os.path.join(self._tmpdir, runner.USER_SCRIPT)
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(source)

        cmd = runner._build_cmd(script)  # [ejecutable, *args, script]
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        env.insert("PYTHONUNBUFFERED", "1")  # salida inmediata (para los prompts de input)

        self._proc = QProcess(self)
        self._proc.setProcessEnvironment(env)
        self._proc.readyReadStandardOutput.connect(self._read_out)
        self._proc.readyReadStandardError.connect(self._read_err)
        self._proc.finished.connect(self._on_finished)
        self._proc.start(cmd[0], cmd[1:])

    def send(self, text: str) -> None:
        """Envía una línea por la entrada estándar del proceso."""
        if self.is_running():
            self._proc.write((text + "\n").encode("utf-8"))

    def stop(self) -> None:
        if self.is_running():
            self._proc.kill()
            self._proc.waitForFinished(1000)

    # ------------------------------------------------------------------ #
    def _read_out(self) -> None:
        data = bytes(self._proc.readAllStandardOutput()).decode("utf-8", "replace")
        if data:
            self.output.emit(data)

    def _read_err(self) -> None:
        data = bytes(self._proc.readAllStandardError()).decode("utf-8", "replace")
        if data:
            self.err_buffer += data
            self.errored.emit(data)

    def _on_finished(self, code: int, _status=None) -> None:
        # vacía lo que quede en los búferes antes de avisar
        self._read_out()
        self._read_err()
        self.done.emit(int(code))
        self._cleanup()

    def _cleanup(self) -> None:
        if self._tmpdir:
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None

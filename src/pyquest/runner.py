"""
runner.py — Motor de ejecución y corrección de código de PyQuest.
runner.py — Code execution & grading engine.

Estrategia "mixta configurable" (la elegida por el usuario):

    1. ANÁLISIS ESTÁTICO (sin ejecutar):
         - ``compile()`` detecta errores de sintaxis / indentación.
         - ``pyflakes`` (opcional) detecta nombres no definidos, imports sin
           usar, variables sin usar, etc. Si no está instalado, se omite.
       Si hay un error de sintaxis NO se ejecuta nada.

    2. EJECUCIÓN REAL en un subproceso aislado con *timeout* (evita que un
       bucle infinito congele la interfaz) y captura de stdout/stderr.

    3. TESTS por ejercicio (stdout, función o arnés de código con asserts).

    4. TRADUCCIÓN de la excepción/traceback a una explicación clara (ES/EN).

Compatibilidad con ejecutables (PyInstaller, modo *one-dir*): cuando la app
está "congelada" no existe un intérprete de Python suelto, así que el propio
ejecutable se relanza a sí mismo con la bandera ``--run-user-script`` y actúa
como un mini-Python. Ese despacho ocurre en ``__main__.py`` ANTES de importar
Qt, por lo que arranca rápido.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from typing import Optional

WORKER_FLAG = "--run-user-script"
USER_SCRIPT = "user_code.py"   # nombre del fichero temporal con el código del alumno
DEFAULT_TIMEOUT = 8.0
MEMORY_LIMIT = 2 * 1024 ** 3      # memoria máxima del código del alumno (2 GB)
FILE_SIZE_LIMIT = 50 * 1024 ** 2  # tamaño máximo de fichero que puede escribir (POSIX)


# --------------------------------------------------------------------------- #
# Estructuras de datos
# --------------------------------------------------------------------------- #
@dataclass
class StaticIssue:
    line: int
    col: int
    severity: str          # "error" | "warning"
    code: str              # "syntax", "undefined-name", "unused-import", ...
    message_es: str
    message_en: str

    def message(self, lang: str) -> str:
        return self.message_es if lang == "es" else self.message_en


@dataclass
class ExceptionInfo:
    etype: str
    evalue: str
    line: Optional[int]
    explanation_es: str
    explanation_en: str

    def explanation(self, lang: str) -> str:
        return self.explanation_es if lang == "es" else self.explanation_en


@dataclass
class RunResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    timed_out: bool = False
    duration: float = 0.0
    exception: Optional[ExceptionInfo] = None

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and self.exception is None


@dataclass
class TestResult:
    name: str
    passed: bool
    message_es: str = ""
    message_en: str = ""

    def message(self, lang: str) -> str:
        return self.message_es if lang == "es" else self.message_en


@dataclass
class Evaluation:
    static_issues: list[StaticIssue] = field(default_factory=list)
    run: Optional[RunResult] = None
    tests: list[TestResult] = field(default_factory=list)

    @property
    def has_syntax_error(self) -> bool:
        return any(i.code == "syntax" for i in self.static_issues)

    @property
    def has_tests(self) -> bool:
        return bool(self.tests)

    @property
    def all_tests_passed(self) -> bool:
        return bool(self.tests) and all(t.passed for t in self.tests)


# --------------------------------------------------------------------------- #
# 1) Análisis estático
# --------------------------------------------------------------------------- #
def analyze_static(source: str) -> list[StaticIssue]:
    """Comprueba sintaxis (siempre) y, si está disponible, pasa pyflakes."""
    issues: list[StaticIssue] = []
    try:
        compile(source, "<pyquest>", "exec")
    except SyntaxError as e:
        line = e.lineno or 1
        col = e.offset or 1
        msg = e.msg or "invalid syntax"
        issues.append(
            StaticIssue(
                line=line,
                col=col,
                severity="error",
                code="syntax",
                message_es=f"Error de sintaxis en la línea {line}: {msg}.",
                message_en=f"Syntax error on line {line}: {msg}.",
            )
        )
        return issues  # sin sintaxis válida no seguimos analizando
    issues.extend(_pyflakes_issues(source))
    return issues


def _pyflakes_issues(source: str) -> list[StaticIssue]:
    try:
        from pyflakes import api as pf_api  # type: ignore
    except Exception:
        return []

    collected = []

    class _Reporter:
        def unexpectedError(self, filename, msg):  # noqa: N802
            pass

        def syntaxError(self, filename, msg, lineno, offset, text):  # noqa: N802
            pass

        def flake(self, message):
            collected.append(message)

    try:
        pf_api.check(source, "<pyquest>", _Reporter())
    except Exception:
        return []

    issues = []
    for m in collected:
        line = getattr(m, "lineno", 1) or 1
        col = (getattr(m, "col", 0) or 0) + 1
        es, en, sev, code = _translate_flake(m)
        issues.append(StaticIssue(line, col, sev, code, es, en))
    return issues


def _translate_flake(m) -> tuple[str, str, str, str]:
    cls = type(m).__name__
    args = getattr(m, "message_args", ()) or ()
    try:
        raw = m.message % args
    except Exception:
        raw = getattr(m, "message", "lint")
    a0 = args[0] if args else "?"

    table = {
        "UndefinedName": (
            f"Nombre no definido: '{a0}'. ¿Lo escribiste mal o no lo creaste antes de usarlo?",
            f"Undefined name: '{a0}'. Did you misspell it or use it before defining it?",
            "error", "undefined-name"),
        "UnusedImport": (
            f"Importas '{a0}' pero nunca lo usas.",
            f"'{a0}' is imported but never used.",
            "warning", "unused-import"),
        "UnusedVariable": (
            f"La variable local '{a0}' se asigna pero no se usa.",
            f"Local variable '{a0}' is assigned but never used.",
            "warning", "unused-variable"),
        "RedefinedWhileUnused": (
            f"Redefines '{a0}' antes de haberlo usado.",
            f"Redefinition of unused '{a0}'.",
            "warning", "redefined"),
        "ImportStarUsed": (
            "Usar 'from módulo import *' oculta de dónde vienen los nombres; evítalo.",
            "'from module import *' hides where names come from; avoid it.",
            "warning", "import-star"),
        "FStringMissingPlaceholders": (
            "f-string sin ningún {campo}: probablemente olvidaste interpolar algo.",
            "f-string without any {placeholders}: you may have forgotten to interpolate.",
            "warning", "fstring"),
    }
    if cls in table:
        return table[cls]
    return (raw, raw, "warning", "lint")


# --------------------------------------------------------------------------- #
# 2) Ejecución real en subproceso
# --------------------------------------------------------------------------- #
def _build_cmd(script_path: str) -> list[str]:
    if getattr(sys, "frozen", False):
        # Ejecutable PyInstaller: nos relanzamos como "mini-Python".
        return [sys.executable, WORKER_FLAG, script_path]
    # Desarrollo: -I aísla del entorno; -c importa PyQuest y ejecuta el MISMO
    # worker que usa el ejecutable (sandbox incluido), así ambos modos se comportan igual.
    return [sys.executable, "-I", "-X", "utf8", "-c", _BOOTSTRAP, _SRC_DIR, script_path]


def _limit_resources() -> None:  # pragma: no cover  (se ejecuta en el hijo)
    """Limita al propio proceso del alumno antes de ejecutar su código.

    Se aplica DENTRO del worker, así vale igual en desarrollo, instalado con pip
    y en el ejecutable, y tanto al comprobar como en el modo interactivo. Mejor
    esfuerzo: un límite que no se pueda aplicar se ignora sin abortar.

    - Windows: el proceso se mete en un *Job Object* con un tope de memoria y
      sin permiso para crear procesos (corta también ``os.startfile``,
      ``multiprocessing`` o ``ctypes``, que esquivan el parche de ``subprocess``).
    - POSIX: ``setrlimit`` de memoria (RLIMIT_AS) y tamaño de fichero.
      (El tiempo ya lo controla el *timeout* de quien lanza el proceso.)
    """
    if sys.platform == "win32":
        try:
            _limit_windows_job()
        except Exception:
            pass
        return
    try:
        import resource
    except ImportError:
        return
    for limit, value in ((resource.RLIMIT_AS, MEMORY_LIMIT), (resource.RLIMIT_FSIZE, FILE_SIZE_LIMIT)):
        try:
            soft, hard = resource.getrlimit(limit)
            if hard != resource.RLIM_INFINITY:
                value = min(value, hard)
            resource.setrlimit(limit, (value, hard))
        except Exception:
            pass


def _limit_windows_job() -> None:  # pragma: no cover  (solo Windows, en el hijo)
    import ctypes
    from ctypes import wintypes

    class _BasicLimits(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _IoCounters(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in (
            "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class _ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _BasicLimits),
            ("IoInfo", _IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x0008
    JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x0100
    JobObjectExtendedLimitInformation = 9

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateJobObjectW.restype = wintypes.HANDLE
    k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    k32.SetInformationJobObject.restype = wintypes.BOOL
    k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    k32.AssignProcessToJobObject.restype = wintypes.BOOL
    k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    k32.GetCurrentProcess.restype = wintypes.HANDLE

    job = k32.CreateJobObjectW(None, None)
    if not job:
        return
    info = _ExtendedLimits()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_ACTIVE_PROCESS
    info.BasicLimitInformation.ActiveProcessLimit = 1  # solo este proceso: no puede crear otros
    info.ProcessMemoryLimit = MEMORY_LIMIT
    if k32.SetInformationJobObject(job, JobObjectExtendedLimitInformation,
                                   ctypes.byref(info), ctypes.sizeof(info)):
        k32.AssignProcessToJobObject(job, k32.GetCurrentProcess())
    # El handle del job se deja abierto a propósito: vive lo que viva el proceso.


def _is_local_address(address) -> bool:
    """True si la dirección de un ``connect()`` es local (loopback o AF_UNIX)."""
    if not isinstance(address, tuple) or not address:
        return True  # AF_UNIX (una ruta) u otras familias que no salen de la máquina
    host = str(address[0]).strip("[]").lower()
    return host in ("localhost", "::1") or host.startswith("127.")


def _install_sandbox(base: str) -> None:  # pragma: no cover (se ejecuta en el hijo)
    """Bloquea red externa, subprocesos y escritura fuera de ``base`` (mejor esfuerzo).

    Dos detalles para no romper la librería estándar (sobre todo ``asyncio`` en
    Windows, que hereda de ``subprocess.Popen`` y crea un par de sockets
    conectados a 127.0.0.1 para su bucle de eventos):

    - ``Popen`` se sustituye por una *subclase* que falla al instanciarse, no por
      una función, para que se pueda seguir heredando de ella.
    - Las conexiones locales (loopback / AF_UNIX) se permiten; solo se bloquean
      las que salen de la máquina.
    """
    import builtins
    import os as _os
    orig_open = builtins.open

    def _bloq(*a, **k):
        raise PermissionError("Operación bloqueada por el sandbox de PyQuest")

    try:
        import socket
        orig_connect = socket.socket.connect
        orig_connect_ex = socket.socket.connect_ex

        def _check_addr(address):
            if not _is_local_address(address):
                raise PermissionError("Conexión de red bloqueada por el sandbox de PyQuest")

        def _connect(self, address):
            _check_addr(address)
            return orig_connect(self, address)

        def _connect_ex(self, address):
            _check_addr(address)
            return orig_connect_ex(self, address)

        # create_connection() usa connect() por dentro, así que queda cubierto.
        socket.socket.connect = _connect
        socket.socket.connect_ex = _connect_ex
    except Exception:
        pass
    try:
        import subprocess

        class _BlockedPopen(subprocess.Popen):
            def __init__(self, *a, **k):
                _bloq()

        subprocess.Popen = _BlockedPopen
        for _n in ("run", "call", "check_call", "check_output", "getoutput", "getstatusoutput"):
            if hasattr(subprocess, _n):
                setattr(subprocess, _n, _bloq)
    except Exception:
        pass
    # Otras formas de lanzar procesos. En Windows el Job Object de _limit_resources
    # ya las impide a nivel de sistema; esto da un mensaje claro en vez de
    # "WinError 1816: cuota insuficiente" (y es la única barrera en POSIX).
    for _n in ("system", "popen", "startfile", "fork", "forkpty", "posix_spawn", "posix_spawnp",
               "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
               "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe"):
        if hasattr(_os, _n):
            try:
                setattr(_os, _n, _bloq)
            except Exception:
                pass
    for _mod, _fn in (("_winapi", "CreateProcess"), ("_posixsubprocess", "fork_exec")):
        try:  # lo que usan por debajo subprocess y multiprocessing (spawn)
            setattr(__import__(_mod), _fn, _bloq)
        except Exception:
            pass
    base_abs = _os.path.normcase(_os.path.abspath(base))

    def _open_seguro(file, mode="r", *args, **kwargs):
        if isinstance(mode, str) and any(c in mode for c in "wax+"):
            try:
                target = _os.path.normcase(_os.path.abspath(_os.fspath(file)))
                # dentro de la carpeta (no basta con empezar igual: /tmp/a vs /tmp/ab)
                fuera = target != base_abs and not target.startswith(base_abs + _os.sep)
            except Exception:
                fuera = not isinstance(file, int)  # un descriptor ya abierto se permite
            if fuera:
                raise PermissionError("Escritura de ficheros fuera del área de trabajo bloqueada")
        return orig_open(file, mode, *args, **kwargs)
    builtins.open = _open_seguro
    try:
        import io
        io.open = _open_seguro  # pathlib (Path.write_text, Path.open) usa io.open
    except Exception:
        pass
    try:
        import tempfile
        tempfile.tempdir = base  # los temporales del alumno, dentro de su carpeta de trabajo
    except Exception:
        pass


# Carpeta que contiene el paquete ``pyquest`` (``src/`` en desarrollo o
# ``site-packages`` si se instaló con pip). Se pasa al subproceso porque ``-I``
# ignora PYTHONPATH.
_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Arranque del subproceso en modo desarrollo: importa PyQuest y ejecuta el mismo
# worker que el ejecutable congelado (sandbox, números de línea y traceback limpio).
# argv: ["-c", <_SRC_DIR>, <script>]
_BOOTSTRAP = (
    "import sys\n"
    "sys.path.insert(0, sys.argv.pop(1))\n"
    "from pyquest.runner import run_user_script_worker\n"
    "run_user_script_worker(sys.argv[1])\n"
)


def run_code(source: str, stdin: str = "", timeout: float = DEFAULT_TIMEOUT) -> RunResult:
    """Ejecuta ``source`` en un subproceso aislado y devuelve el resultado."""
    with tempfile.TemporaryDirectory(prefix="pyquest_") as td:
        script = os.path.join(td, USER_SCRIPT)
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(source)

        cmd = _build_cmd(script)
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        # (los límites de memoria/procesos los aplica el propio worker: ver _limit_resources)
        start = time.time()
        try:
            proc = subprocess.run(
                cmd,
                input=stdin.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                cwd=td,
                env=env,
            )
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or b"").decode("utf-8", "replace")
            return RunResult(
                stdout=out, stderr="", exit_code=-1, timed_out=True,
                duration=timeout, exception=_timeout_exception(),
            )

        duration = time.time() - start
        out = proc.stdout.decode("utf-8", "replace")
        err = proc.stderr.decode("utf-8", "replace")
        err = err.replace(td + os.sep, "").replace(td, "")  # oculta la ruta temporal
        exc = parse_exception(err) if proc.returncode != 0 else None
        return RunResult(
            stdout=out, stderr=err, exit_code=proc.returncode,
            timed_out=False, duration=duration, exception=exc,
        )


# --------------------------------------------------------------------------- #
# Traducción de excepciones / tracebacks
# --------------------------------------------------------------------------- #
_FRAME_RE = re.compile(r'File "([^"]*)", line (\d+)')


def _is_user_file(filename: str) -> bool:
    """True si el marco del traceback pertenece al script del alumno."""
    return filename.replace("\\", "/").rsplit("/", 1)[-1] == USER_SCRIPT


def parse_exception(stderr: str) -> Optional[ExceptionInfo]:
    """Extrae tipo, mensaje y línea de un traceback de Python."""
    text = stderr.strip()
    if not text:
        return None
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None

    last = lines[-1].strip()
    if ":" in last:
        etype, _, evalue = last.partition(":")
        etype, evalue = etype.strip(), evalue.strip()
    else:
        etype, evalue = last.strip(), ""

    # solo nos quedamos con el nombre corto de la excepción
    etype = etype.split(".")[-1]
    if not re.match(r"^[A-Za-z_]\w*$", etype):
        return None

    # La línea que interesa es la del ÚLTIMO marco del código del alumno: los
    # marcos de la librería estándar (p. ej. asyncio/__init__.py, línea 133) no
    # corresponden a nada que se vea en el editor.
    line = None
    for m in _FRAME_RE.finditer(stderr):
        if _is_user_file(m.group(1)):
            line = int(m.group(2))

    es, en = explain_exception(etype, evalue, line)
    return ExceptionInfo(etype, evalue, line, es, en)


def _timeout_exception() -> ExceptionInfo:
    return ExceptionInfo(
        etype="TimeoutError",
        evalue="",
        line=None,
        explanation_es=("Tu programa tardó demasiado y se detuvo. La causa más "
                        "común es un bucle que nunca termina (revisa la condición "
                        "del while o que algo cambie dentro del bucle)."),
        explanation_en=("Your program took too long and was stopped. The most "
                        "common cause is a loop that never ends (check the while "
                        "condition or that something changes inside the loop)."),
    )


_EXC_HELP: dict[str, tuple[str, str]] = {
    "SyntaxError": (
        "Sintaxis inválida: Python no entiende la estructura. Revisa los dos puntos ':', "
        "los paréntesis y comillas sin cerrar.",
        "Invalid syntax: Python can't parse the structure. Check colons ':', and "
        "unclosed parentheses or quotes."),
    "IndentationError": (
        "Indentación incorrecta. En Python los bloques se delimitan con sangría "
        "(usa 4 espacios) y debe ser consistente.",
        "Bad indentation. In Python blocks are defined by indentation (use 4 spaces) "
        "and it must be consistent."),
    "NameError": (
        "Usas un nombre que no existe todavía. ¿Lo definiste antes? ¿Hay una errata?",
        "You use a name that doesn't exist yet. Did you define it earlier? A typo?"),
    "TypeError": (
        "Operación entre tipos incompatibles (p. ej. sumar texto y número) o número "
        "de argumentos incorrecto en una función.",
        "Operation between incompatible types (e.g. adding text and a number) or a "
        "wrong number of function arguments."),
    "ValueError": (
        "El tipo es correcto pero el valor no es válido (p. ej. int('hola')).",
        "The type is right but the value is invalid (e.g. int('hello'))."),
    "IndexError": (
        "Accedes a una posición que no existe en la lista/cadena. Recuerda que el "
        "primer índice es 0 y el último es len(x)-1.",
        "You access a position that doesn't exist in the list/string. Remember the "
        "first index is 0 and the last is len(x)-1."),
    "KeyError": (
        "Pides una clave que no está en el diccionario. Comprueba el nombre exacto "
        "o usa dic.get(clave).",
        "You request a key that isn't in the dictionary. Check the exact name or use "
        "dict.get(key)."),
    "ZeroDivisionError": (
        "División entre cero. Asegúrate de que el divisor no sea 0 antes de dividir.",
        "Division by zero. Make sure the divisor isn't 0 before dividing."),
    "AttributeError": (
        "Llamas a un método/atributo que ese objeto no tiene. Revisa el tipo del "
        "objeto y el nombre del método.",
        "You call a method/attribute the object doesn't have. Check the object type "
        "and the method name."),
    "ImportError": (
        "No se pudo importar el módulo. ¿Está bien escrito el nombre?",
        "The module couldn't be imported. Is the name spelled correctly?"),
    "ModuleNotFoundError": (
        "Ese módulo no existe o no está instalado.",
        "That module doesn't exist or isn't installed."),
    "AssertionError": (
        "Una comprobación (assert) falló: el resultado no es el esperado.",
        "An assertion failed: the result is not what was expected."),
    "RecursionError": (
        "Demasiadas llamadas recursivas: probablemente falta el caso base.",
        "Too many recursive calls: the base case is probably missing."),
    "MemoryError": (
        "Tu programa intentó usar demasiada memoria (PyQuest lo limita a 2 GB). Revisa si "
        "creas listas o cadenas enormes, o un bucle que no para de añadir elementos.",
        "Your program tried to use too much memory (PyQuest caps it at 2 GB). Check for huge "
        "lists or strings, or a loop that keeps appending items."),
    "PermissionError": (
        "Operación no permitida. En PyQuest el código no puede conectarse a internet, lanzar "
        "otros programas ni escribir fuera de su carpeta de trabajo.",
        "Operation not allowed. In PyQuest code can't connect to the internet, start other "
        "programs or write outside its working folder."),
}


def explain_exception(etype: str, evalue: str, line: Optional[int]) -> tuple[str, str]:
    base_es, base_en = _EXC_HELP.get(
        etype,
        (f"Se produjo una excepción {etype}.", f"An {etype} exception occurred."),
    )
    where_es = f" (línea {line})" if line else ""
    where_en = f" (line {line})" if line else ""
    val = f" → {evalue}" if evalue else ""
    es = f"{etype}{where_es}: {base_es}{val}"
    en = f"{etype}{where_en}: {base_en}{val}"
    return es, en


# --------------------------------------------------------------------------- #
# 3) Tests por ejercicio
# --------------------------------------------------------------------------- #
def run_tests(source: str, tests: list[dict], timeout: float = DEFAULT_TIMEOUT) -> list[TestResult]:
    results: list[TestResult] = []
    for i, t in enumerate(tests):
        name = t.get("name") or f"Test {i + 1}"
        ttype = t.get("type", "code")
        if ttype == "stdout":
            r = _test_stdout(source, t, timeout)
        elif ttype == "function":
            r = _test_function(source, t, timeout)
        else:
            r = _test_code(source, t, timeout)
        r.name = name
        results.append(r)
    return results


def _normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def _compare(got: str, expected: str, match: str) -> bool:
    if match == "exact":
        return got == expected
    if match == "contains":
        return expected.strip() in got
    return _normalize(got) == _normalize(expected)  # "normalized" (por defecto)


def _fail_from_run(rr: RunResult, lang_msgs: tuple[str, str] | None = None) -> Optional[TestResult]:
    """Si la ejecución falló (timeout/excepción), devuelve un TestResult de fallo."""
    if rr.timed_out:
        return TestResult("", False,
                          message_es=rr.exception.explanation_es if rr.exception else "Tiempo agotado.",
                          message_en=rr.exception.explanation_en if rr.exception else "Timed out.")
    if rr.exception is not None:
        return TestResult("", False,
                          message_es=rr.exception.explanation_es,
                          message_en=rr.exception.explanation_en)
    return None


def _test_stdout(source: str, t: dict, timeout: float) -> TestResult:
    rr = run_code(source, stdin=t.get("stdin", ""), timeout=timeout)
    failed = _fail_from_run(rr)
    if failed:
        return failed
    expected = t.get("expected", "")
    if isinstance(expected, list):
        expected = "\n".join(str(x) for x in expected)
    match = t.get("match", "normalized")
    if _compare(rr.stdout, expected, match):
        return TestResult("", True,
                          message_es="Salida correcta.", message_en="Correct output.")
    return TestResult(
        "", False,
        message_es=f"Salida esperada:\n{expected}\n— pero obtuve:\n{rr.stdout.strip()}",
        message_en=f"Expected output:\n{expected}\n— but got:\n{rr.stdout.strip()}",
    )


def _test_code(source: str, t: dict, timeout: float) -> TestResult:
    harness = t.get("harness", "")
    full = source + "\n\n# --- PyQuest: comprobación / check ---\n" + harness
    rr = run_code(full, stdin=t.get("stdin", ""), timeout=timeout)
    failed = _fail_from_run(rr)
    if failed:
        # Si el ejercicio define mensajes propios, los preferimos.
        if t.get("message_es") or t.get("message_en"):
            return TestResult("", False,
                              message_es=t.get("message_es", failed.message_es),
                              message_en=t.get("message_en", failed.message_en))
        return failed
    return TestResult("", True, message_es="Correcto.", message_en="Correct.")


def _test_function(source: str, t: dict, timeout: float) -> TestResult:
    """
    Genera un arnés con asserts para una función definida por el usuario.

    Los argumentos y el resultado esperado se serializan con ``repr`` (literales
    de Python seguros), de modo que valores con comillas, listas o diccionarios
    no rompen el arnés.
    """
    fname = t["function"]
    cases = t.get("cases", [])
    lines = []
    for idx, c in enumerate(cases, 1):
        args_lit = repr(tuple(c.get("args", [])))
        kwargs_lit = repr(dict(c.get("kwargs", {})))
        expected_lit = repr(c.get("expected"))
        lines.append(
            f"__args = {args_lit}\n"
            f"__kwargs = {kwargs_lit}\n"
            f"__exp = {expected_lit}\n"
            f"__got = {fname}(*__args, **__kwargs)\n"
            f'assert __got == __exp, '
            f'"caso {idx} -> {fname}" + repr(__args) + ": esperaba " '
            f'+ repr(__exp) + " pero obtuve " + repr(__got)\n'
        )
    harness = "\n".join(lines)
    return _test_code(source, {**t, "harness": harness}, timeout)


# --------------------------------------------------------------------------- #
# API de alto nivel usada por la GUI
# --------------------------------------------------------------------------- #
def evaluate(source: str, exercise: dict, timeout: float = DEFAULT_TIMEOUT) -> Evaluation:
    """
    Flujo "mixto": análisis estático -> (si compila) ejecución + tests.
    """
    ev = Evaluation()
    ev.static_issues = analyze_static(source)
    if ev.has_syntax_error:
        return ev
    tests = exercise.get("tests", [])
    if tests:
        ev.tests = run_tests(source, tests, timeout)
    else:
        ev.run = run_code(source, timeout=timeout)
    return ev


# --------------------------------------------------------------------------- #
# Modo "worker": ejecuta un script como lo haría `python script.py`
# (lo usa el ejecutable congelado al relanzarse a sí mismo)
# --------------------------------------------------------------------------- #
def run_user_script_worker(path: str) -> None:
    """
    Ejecuta el archivo ``path`` imitando a ``python path``: ``__name__`` es
    ``"__main__"`` y los tracebacks referencian el archivo del usuario. Si hay
    una excepción, imprime un traceback limpio (sin los marcos internos de
    PyQuest) y sale con código 1.
    """
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    _limit_resources()
    _install_sandbox(os.path.dirname(os.path.abspath(path)))
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    g = {"__name__": "__main__", "__file__": path, "__builtins__": __builtins__}
    sys.argv = [path]
    try:
        # compile() va dentro del try para que un error de sintaxis (p. ej. en el
        # modo interactivo) se muestre sin los marcos internos de PyQuest.
        # dont_inherit=True: que el "from __future__ import annotations" de este
        # módulo NO se aplique al código del alumno (sus anotaciones serían texto).
        exec(compile(src, path, "exec", dont_inherit=True), g)
    except SystemExit:
        raise
    except BaseException:
        exc_type, exc, tb = sys.exc_info()
        # tb.tb_next salta el marco de este exec() para que el traceback
        # empiece en el código del usuario, como en python normal.
        traceback.print_exception(exc_type, exc, tb.tb_next if tb else tb)
        sys.exit(1)

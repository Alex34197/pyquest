# Changelog / Registro de cambios

Todas las versiones notables de PyQuest. Formato basado en *Keep a Changelog*.

## [1.1.0] — 2026-11-19

Primera versión publicada en GitHub. Incluye también todo lo de 1.0.1.

### Añadido
- **Borradores automáticos**: el código a medias se guarda al cambiar de ejercicio o de
  lección, al cerrar la app y al exportar, y se recupera al volver.
- **Ver la solución ya no regala XP**: el ejercicio cuenta como resuelto, pero sin XP (se
  avisa antes de mostrarla).
- **Examen corregido pregunta a pregunta**: ✓/✗ en cada una, la respuesta correcta de las
  falladas y botón **Nuevo intento** (vuelve a barajar).
- **Límites del sistema para el código del alumno**: tope de 2 GB de memoria (Windows: *Job
  Object*; Linux: `RLIMIT_AS`) y, en Windows, prohibido crear procesos a nivel de sistema.
  Explicaciones nuevas para `MemoryError` y `PermissionError`.
- Instalación con **`pip install .`** (comando `pyquest`): el contenido viaja dentro del
  paquete (`src/pyquest/course/`).
- Capturas, sección de descargas y badges en el README.

### Corregido
- **Importar progreso** no traducía los menús ni aplicaba scanlines, tamaño de fuente o el tema
  marcado, y aceptaba datos con tipos incorrectos. Ahora todo progreso (cargado o importado)
  se valida y se aplica entero a la interfaz.
- Un `progress.json` corrupto ya no se pierde: se aparta como `progress.corrupt.json`.
- Las listas del progreso compartían objeto con los valores por defecto (copia superficial).
- Sandbox: `pathlib` y las carpetas "hermanas" (`/tmp/a` vs `/tmp/ab`) esquivaban el bloqueo
  de escritura; `os.startfile`, `_winapi.CreateProcess`, `os.spawn*`/`exec*`/`fork` podían
  lanzar procesos. `tempfile` ahora escribe en la carpeta de trabajo.
- Una salida enorme (p. ej. `print` en un bucle infinito) podía congelar la consola: ahora
  guarda como mucho 5000 líneas y recorta bloques gigantes.
- En los botones de opción del examen desaparecía el círculo de la opción marcada al
  deshabilitarse.

### Interno
- CI: tests en **Windows, macOS y Linux** con Python 3.10 y 3.13 en cada *push* y *pull
  request*; la compilación y la Release solo con etiquetas `v*`.
- Los tests ya no tocan el progreso real del usuario (fixture en `conftest.py`).
- Repositorio git con `.gitignore` y `.gitattributes` completos.

## [1.0.1] — 2026-11-19

Versión de correcciones (no publicada por separado).

### Corregido
- **Ejercicios de `asyncio` (módulos 51–52) imposibles de resolver en Windows**: el sandbox
  sustituía `subprocess.Popen` por una función (y `asyncio` hereda de ella) y bloqueaba también
  las conexiones locales que su bucle de eventos necesita. Ahora `Popen` es una subclase que
  falla al instanciarse y solo se bloquean las conexiones que salen de la máquina.
- **Ejecutable sin parte de la librería estándar**: `sqlite3`, `configparser`, `uuid`,
  `zoneinfo`, `timeit`, `xml`… daban `ModuleNotFoundError` solo en la versión compilada
  (módulos 27 y 70 entre otros). Los `.spec` incluyen ahora toda la librería estándar.
- **Anotaciones de tipos convertidas en texto en el ejecutable** (`'int'` en vez de `int`,
  ejercicio del módulo 11): el `from __future__ import annotations` del motor se contagiaba al
  código del alumno.
- **Línea del error equivocada**: se resaltaba la línea de la librería estándar (p. ej. 133) en
  lugar de la del código del alumno. Los errores de sintaxis del modo interactivo ya no muestran
  marcos internos de PyQuest.
- **Ejercicio equivocado marcado como resuelto** si se cambiaba de ejercicio o de lección
  mientras se comprobaba. Ahora el resultado se asigna al ejercicio (y al código) que se envió, y
  la navegación se bloquea durante la comprobación.
- **Posible cierre inesperado** al pulsar `Ctrl+Intro` dos veces seguidas o al cerrar la ventana
  durante una comprobación.

### Interno
- Desarrollo y ejecutable usan el mismo código de sandbox (antes estaba duplicado).
- Nuevos tests del sandbox, de la línea del error y de la comprobación en la interfaz.

## [1.0.0] — 2026-06-12

Primera versión estable.

### Contenido
- **78 módulos · 159 lecciones · 320 ejercicios** bilingües (ES/EN), de cero a experto:
  fundamentos, control de flujo, estructuras de datos, POO (hasta metaclases y descriptores),
  funcional, regex, fechas, seguridad (hashing/secrets/HMAC), `asyncio`, hilos, redes (`ipaddress`),
  algoritmos, programación dinámica y dos mini-proyectos.

### Funcionalidades
- Motor de corrección **mixto**: análisis estático (sintaxis + *pyflakes*) + ejecución real en
  subproceso aislado (con *timeout* y límites de memoria/CPU/ficheros) + tests por ejercicio, con
  **tracebacks traducidos** y resaltado de la línea del error.
- **Playground / REPL** con `input()` en vivo e historial de comandos.
- **Examen final** de autoevaluación (30 preguntas, **barajadas** en cada intento).
- **Gamificación**: XP, racha y logros.
- **Mi progreso** con gráfica de barras, **repaso de fallados**, **marcadores (★)**,
  **exportar/importar** progreso, y memoria de la última lección y el tamaño de ventana.
- **4 temas** (verde fósforo, ámbar, MS-DOS azul, claro), **buscador** robusto
  (sin acentos, multi-palabra y por nombre de módulo), editor con números de línea,
  resaltado, comentar (`Ctrl+/`) e indentar/desindentar la selección.
- **Bilingüe ES/EN** conmutable en caliente.

### Empaquetado y calidad
- Ejecutables para **Windows, macOS y Linux** (one-dir, one-file portable e instaladores
  `.exe`/`.dmg`/`.deb`), firma de código documentada en `SIGNING.md`.
- **CI** (GitHub Actions): `ruff`, tests (`pytest`, incl. humo de GUI) y compilación en los 3 SO.

### Requisitos
- **Python 3.10+** (por `match/case` y `asyncio` moderno).

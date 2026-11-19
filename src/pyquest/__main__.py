"""
__main__.py — punto de entrada de PyQuest.
__main__.py — PyQuest entry point.

IMPORTANTE: el "modo worker" (--run-user-script) se atiende ANTES de importar
Qt, para que el ejecutable congelado se relance rápido al ejecutar el código
del usuario.  ``python -m pyquest`` lanza la interfaz gráfica.
"""
from __future__ import annotations

import sys


def main() -> int:
    # 1) ¿Nos han relanzado para ejecutar el código del usuario? (binario congelado)
    if len(sys.argv) >= 3 and sys.argv[1] == "--run-user-script":
        from .runner import run_user_script_worker
        run_user_script_worker(sys.argv[2])
        return 0

    # 2) Modo normal: interfaz gráfica
    from .app import run_app
    return run_app(sys.argv)


if __name__ == "__main__":
    sys.exit(main())

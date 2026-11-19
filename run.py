#!/usr/bin/env python3
"""
run.py — lanzador para desarrollo (sin instalar nada).
run.py — development launcher (no install needed).

    python run.py            # abre la interfaz gráfica
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from pyquest.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

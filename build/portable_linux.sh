#!/usr/bin/env bash
# ============================================================
#  PyQuest PORTABLE (Linux): genera UN SOLO archivo independiente.
#  Ejecuta:  bash build/portable_linux.sh
#  Resultado:  dist/PyQuest  (un unico archivo, copialo donde quieras)
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

rm -rf dist
pyinstaller --noconfirm PyQuest-onefile.spec

echo
echo "================================================================"
echo "  TU ARCHIVO INDEPENDIENTE ES:   dist/PyQuest"
echo "  Copia SOLO ese archivo a otro Linux del mismo tipo y ejecuta:"
echo "      chmod +x PyQuest && ./PyQuest"
echo "  (NO uses la carpeta dist/PyQuest/ , esa es la version carpeta.)"
echo "================================================================"

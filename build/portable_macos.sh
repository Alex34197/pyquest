#!/usr/bin/env bash
# ============================================================
#  PyQuest PORTABLE (macOS): genera UN SOLO archivo independiente.
#  Ejecuta:  bash build/portable_macos.sh
#  Resultado:  dist/PyQuest  (un unico ejecutable; no es un .app, es un binario suelto)
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

# Firma ad-hoc para poder abrirlo sin el aviso "app dañada".
if [ -f "dist/PyQuest" ]; then
  codesign --force --options runtime -s - "dist/PyQuest" || true
fi

echo
echo "================================================================"
echo "  TU ARCHIVO INDEPENDIENTE ES:   dist/PyQuest"
echo "  Copia SOLO ese archivo. La primera vez: clic derecho -> Abrir."
echo "================================================================"

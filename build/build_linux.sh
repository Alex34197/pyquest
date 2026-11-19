#!/usr/bin/env bash
# Construye el ejecutable de PyQuest para Linux (Debian/Ubuntu y derivados).
# Builds the PyQuest executable for Linux.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

# build_linux.sh           -> carpeta dist/PyQuest/ (one-dir, mas agil)
# build_linux.sh onefile   -> UN archivo dist/PyQuest (portable)
SPEC=PyQuest.spec
[ "${1:-}" = "onefile" ] && SPEC=PyQuest-onefile.spec
pyinstaller --noconfirm "$SPEC"

echo
echo "================================================================"
echo " one-dir:  dist/PyQuest/PyQuest   (mueve la CARPETA dist/PyQuest)"
echo " onefile:  dist/PyQuest           (UN archivo portable; usa: build_linux.sh onefile)"
echo "================================================================"

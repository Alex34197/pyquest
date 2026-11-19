#!/usr/bin/env bash
# Construye PyQuest.app para macOS.
# Builds PyQuest.app for macOS.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

# build_macos.sh           -> dist/PyQuest.app (one-dir, recomendado en macOS)
# build_macos.sh onefile   -> UN archivo dist/PyQuest (portable)
SPEC=PyQuest.spec
[ "${1:-}" = "onefile" ] && SPEC=PyQuest-onefile.spec
pyinstaller --noconfirm "$SPEC"

# Firma ad-hoc (gratis): permite ejecutar la app en tu Mac sin el aviso "app dañada".
# Para DISTRIBUIR a otros hace falta un "Developer ID" + notarización (ver SIGNING.md).
if [ -d "dist/PyQuest.app" ]; then
  codesign --deep --force --options runtime -s - "dist/PyQuest.app" \
    && echo "Firma ad-hoc aplicada a dist/PyQuest.app"
elif [ -f "dist/PyQuest" ]; then
  codesign --force --options runtime -s - "dist/PyQuest" \
    && echo "Firma ad-hoc aplicada a dist/PyQuest (onefile)"
fi

# --- Firma real con Developer ID (descomenta y rellena DEV_ID) ---
# DEV_ID="Developer ID Application: Tu Nombre (TEAMID)"
# codesign --deep --force --options runtime --timestamp -s "$DEV_ID" "dist/PyQuest.app"
# xcrun notarytool submit dist/PyQuest.app --keychain-profile "AC_PASSWORD" --wait
# xcrun stapler staple "dist/PyQuest.app"

echo
echo "================================================================"
echo " OK  ->  dist/PyQuest.app   (y dist/PyQuest/)"
echo " Para distribuir:  hdiutil create -volname PyQuest -srcfolder dist/PyQuest.app -ov PyQuest-macos.dmg"
echo " Nota: para evitar la advertencia de Gatekeeper habría que firmar/notarizar la app."
echo "================================================================"

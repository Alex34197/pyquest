#!/usr/bin/env bash
# Crea un instalador .dmg para macOS (arrastrar PyQuest a Aplicaciones).
# Create a macOS .dmg installer (drag PyQuest to Applications).
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION=1.1.0
# 1) compila la .app (one-dir) si no existe
[ -d "dist/PyQuest.app" ] || bash build/build_macos.sh

APP="dist/PyQuest.app"
DMG="dist/PyQuest-${VERSION}.dmg"
rm -f "$DMG"

STAGING="$(mktemp -d)"
cp -R "$APP" "$STAGING/"
ln -s /Applications "$STAGING/Applications"   # acceso directo para arrastrar
hdiutil create -volname "PyQuest" -srcfolder "$STAGING" -ov -format UDZO "$DMG"
rm -rf "$STAGING"

echo
echo "DMG creado: $DMG"
echo "El usuario lo abre y arrastra PyQuest a la carpeta Aplicaciones."

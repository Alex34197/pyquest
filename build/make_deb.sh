#!/usr/bin/env bash
# Crea un paquete .deb instalable para Debian/Ubuntu y derivados.
# Build an installable .deb package for Debian/Ubuntu.
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION=1.1.0
ARCH=amd64

# 1) compila la app (one-dir) si no existe
[ -d "dist/PyQuest" ] || bash build/build_linux.sh

PKGDIR="dist/pyquest_${VERSION}_${ARCH}"
rm -rf "$PKGDIR"
mkdir -p "$PKGDIR/DEBIAN" \
         "$PKGDIR/opt/pyquest" \
         "$PKGDIR/usr/share/applications" \
         "$PKGDIR/usr/share/icons/hicolor/256x256/apps" \
         "$PKGDIR/usr/bin"

# binario + datos
cp -r dist/PyQuest/. "$PKGDIR/opt/pyquest/"
cp assets/icon.png "$PKGDIR/usr/share/icons/hicolor/256x256/apps/pyquest.png"

# lanzador de menú
cat > "$PKGDIR/usr/share/applications/pyquest.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=PyQuest
Comment=Aprende Python con teoría y práctica / Learn Python
Exec=/opt/pyquest/PyQuest
Icon=pyquest
Categories=Education;Development;
Terminal=false
DESKTOP

# comando 'pyquest' en la terminal
ln -sf /opt/pyquest/PyQuest "$PKGDIR/usr/bin/pyquest"

# metadatos del paquete (cambia el email del Maintainer si quieres)
cat > "$PKGDIR/DEBIAN/control" <<CONTROL
Package: pyquest
Version: ${VERSION}
Section: education
Priority: optional
Architecture: ${ARCH}
Maintainer: Alex García González <alex@pyquest.local>
Depends: libegl1, libgl1, libxkbcommon0, libglib2.0-0
Description: PyQuest - aprende Python con teoria y practica
 Aplicacion de escritorio para aprender Python con un nucleo teorico
 extenso y ejercicios corregidos automaticamente, estilo terminal retro.
CONTROL

# permisos: legible por cualquier usuario; binario ejecutable
chmod -R go+rX "$PKGDIR/opt" "$PKGDIR/usr"
chmod 755 "$PKGDIR/opt/pyquest/PyQuest"

dpkg-deb --build --root-owner-group "$PKGDIR"
echo
echo ".deb creado: ${PKGDIR}.deb"
echo "Instalar:  sudo apt install ./${PKGDIR}.deb"

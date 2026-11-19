# -*- mode: python ; coding: utf-8 -*-
# Especificación de PyInstaller para PyQuest (modo one-dir).
# PyInstaller spec for PyQuest (one-dir mode).
#
# Construir / Build:   pyinstaller --noconfirm PyQuest.spec
# Resultado / Output:  dist/PyQuest/   (carpeta autocontenida; en macOS, PyQuest.app)
#
# Nota: el modo one-dir es importante. La app se relanza a sí misma con
# --run-user-script para ejecutar el código del usuario; en one-dir ese
# relanzamiento es instantáneo (no re-extrae nada).

import os
import sys

block_cipher = None


def _icon(path):
    """Usa el icono solo si existe; si no, PyInstaller pone el icono por defecto."""
    return path if os.path.exists(path) else None


def _version_file():
    """Recurso de versión de Windows (rellena Propiedades > Detalles; se ignora fuera de Windows)."""
    return 'version_info.txt' if os.path.exists('version_info.txt') else None


def _stdlib_modules():
    """Toda la librería estándar (menos lo que no pinta nada en PyQuest).

    PyInstaller solo empaqueta lo que importa la propia app, pero el alumno
    importa en sus ejercicios lo que enseña el curso (sqlite3, configparser,
    uuid, zoneinfo, timeit...). Sin esto, esos ejercicios fallan SOLO en el
    ejecutable con ModuleNotFoundError.
    """
    import importlib.util
    import pkgutil
    skip = {'tkinter', 'turtle', 'turtledemo', 'idlelib', 'test', 'tests',
            'ensurepip', 'venv', 'lib2to3', 'pydoc_data', 'antigravity'}
    mods = []
    for name in sorted(sys.stdlib_module_names):
        if name.startswith('_') or name in skip:
            continue
        try:
            spec = importlib.util.find_spec(name)
        except Exception:
            continue
        if spec is None:  # módulo de otro sistema operativo
            continue
        mods.append(name)
        if spec.submodule_search_locations:  # paquete: también sus submódulos
            for info in pkgutil.walk_packages(spec.submodule_search_locations, name + '.',
                                              onerror=lambda _n: None):
                if not skip.intersection(info.name.split('.')):
                    mods.append(info.name)
    return mods


a = Analysis(
    ['run.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/pyquest/course', 'pyquest/course'), ('assets', 'assets')],  # teoría/ejercicios + icono
    hiddenimports=['pyflakes', 'pyflakes.api'] + _stdlib_modules(),
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'PySide6.QtWebEngineCore', 'PySide6.QtMultimedia',
              'PySide6.Qt3DCore', 'PySide6.QtCharts', 'PySide6.QtQuick'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PyQuest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # app de ventana (sin consola)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon('assets/icon.ico'),
    version=_version_file(),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PyQuest',
)

# En macOS, empaqueta como .app
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='PyQuest.app',
        icon=_icon('assets/icon.icns'),
        bundle_identifier='com.pyquest.app',
        info_plist={
            'CFBundleName': 'PyQuest',
            'CFBundleDisplayName': 'PyQuest',
            'NSHighResolutionCapable': True,
        },
    )

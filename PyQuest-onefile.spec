# -*- mode: python ; coding: utf-8 -*-
# PyQuest en UN SOLO archivo portable (one-file).
# Single-file portable build of PyQuest (one-file).
#
# Construir / Build:   pyinstaller --noconfirm PyQuest-onefile.spec
# Resultado / Output:  dist/PyQuest.exe  (Windows)  ·  dist/PyQuest  (Linux/macOS)
#   -> un único archivo que puedes copiar entre equipos del MISMO sistema operativo.
#
# Compromiso frente a one-dir (PyQuest.spec): al ejecutarse, el archivo se
# auto-extrae en una carpeta temporal, así que arranca y ejecuta el código del
# usuario algo más lento. Para uso diario intensivo, one-dir es más ágil.

import os
import sys

block_cipher = None


def _icon(path):
    return path if os.path.exists(path) else None


def _version_file():
    return 'version_info.txt' if os.path.exists('version_info.txt') else None


def _stdlib_modules():
    """Toda la librería estándar (menos lo que no pinta nada en PyQuest).

    PyInstaller solo empaqueta lo que importa la propia app, pero el alumno
    importa en sus ejercicios lo que enseña el curso (sqlite3, configparser,
    uuid, zoneinfo, timeit...). Sin esto, esos ejercicios fallan SOLO en el
    ejecutable con ModuleNotFoundError. (Igual que en PyQuest.spec.)
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
    datas=[('src/pyquest/course', 'pyquest/course'), ('assets', 'assets')],
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

# EXE one-file: se incluyen binarios y datos DENTRO del ejecutable (sin COLLECT).
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PyQuest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon('assets/icon.ico'),
    version=_version_file(),
)

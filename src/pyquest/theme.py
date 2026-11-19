"""
theme.py — paletas retro y hoja de estilos (QSS) conmutables.
theme.py — switchable retro palettes and stylesheet.

Temas: verde fósforo (por defecto), ámbar sobre negro y MS-DOS azul.
Las variables de color del módulo (theme.FG, theme.BG, ...) se rellenan desde el
tema activo con set_theme(); así el resto de la app las lee como theme.FG.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# Paletas
# --------------------------------------------------------------------------- #
THEMES = {
    "green": {  # verde fósforo (Unix/Linux)
        "BG": "#0a120c", "BG_ALT": "#0d1812", "PANEL": "#0b1610",
        "GUTTER_BG": "#0c160f", "GUTTER_FG": "#2f7d4f",
        "CURRENT_LINE": "#11271b", "ERROR_LINE_BG": "#3d1620",
        "FG": "#46d977", "FG_BRIGHT": "#9bffc4", "FG_DIM": "#3a9b63",
        "BORDER": "#1c3a28", "SELECTION": "#1d4630",
        "ERROR": "#ff6b6b", "WARN": "#ffce6b", "OK": "#86ffae", "INFO": "#6fd0ff",
        "SYN_KW": "#5fd7ff", "SYN_BUILTIN": "#9bffc4", "SYN_FUNC": "#ffe082",
        "SYN_NUM": "#ffab70", "SYN_STR": "#b8e986", "SYN_COMMENT": "#4f7a5f",
    },
    "amber": {  # ámbar sobre negro
        "BG": "#120c00", "BG_ALT": "#1a1100", "PANEL": "#150e00",
        "GUTTER_BG": "#160f00", "GUTTER_FG": "#8a5e10",
        "CURRENT_LINE": "#2a1c02", "ERROR_LINE_BG": "#3d1606",
        "FG": "#ffb000", "FG_BRIGHT": "#ffd680", "FG_DIM": "#b3791f",
        "BORDER": "#3a2a08", "SELECTION": "#4a3508",
        "ERROR": "#ff6b4a", "WARN": "#ffd54a", "OK": "#ffce7a", "INFO": "#ffcf8a",
        "SYN_KW": "#ffcf5a", "SYN_BUILTIN": "#ffd680", "SYN_FUNC": "#ffe6a8",
        "SYN_NUM": "#ff9f45", "SYN_STR": "#e8c060", "SYN_COMMENT": "#8a6a2a",
    },
    "dos": {  # MS-DOS azul (paleta EGA)
        "BG": "#0000aa", "BG_ALT": "#0000a0", "PANEL": "#0000c4",
        "GUTTER_BG": "#000088", "GUTTER_FG": "#7a7ad0",
        "CURRENT_LINE": "#2222c8", "ERROR_LINE_BG": "#aa0000",
        "FG": "#cacaca", "FG_BRIGHT": "#ffffff", "FG_DIM": "#9a9ad6",
        "BORDER": "#5555cc", "SELECTION": "#2a2ad8",
        "ERROR": "#ff5555", "WARN": "#ffff55", "OK": "#55ff55", "INFO": "#55ffff",
        "SYN_KW": "#ffff55", "SYN_BUILTIN": "#55ffff", "SYN_FUNC": "#ffffff",
        "SYN_NUM": "#ff55ff", "SYN_STR": "#55ff55", "SYN_COMMENT": "#8a8ad0",
    },
    "light": {  # claro (papel)
        "BG": "#f4f1e8", "BG_ALT": "#ffffff", "PANEL": "#eae6da",
        "GUTTER_BG": "#e6e2d6", "GUTTER_FG": "#9a8f70",
        "CURRENT_LINE": "#eef3e8", "ERROR_LINE_BG": "#f6d6d6",
        "FG": "#2a2a2a", "FG_BRIGHT": "#000000", "FG_DIM": "#6a6a5a",
        "BORDER": "#c9c2ad", "SELECTION": "#cfe3d0",
        "ERROR": "#c0392b", "WARN": "#9a6a00", "OK": "#2e7d32", "INFO": "#1565c0",
        "SYN_KW": "#0b66c2", "SYN_BUILTIN": "#2e7d32", "SYN_FUNC": "#8a6d00",
        "SYN_NUM": "#b5651d", "SYN_STR": "#357a38", "SYN_COMMENT": "#8a8a78",
    },
}

THEME_ORDER = ["green", "amber", "dos", "light"]
current_theme = "green"


def set_theme(name: str) -> None:
    """Activa una paleta y publica sus colores como variables del módulo."""
    global current_theme
    if name not in THEMES:
        name = "green"
    current_theme = name
    globals().update(THEMES[name])


set_theme("green")  # inicializa theme.BG, theme.FG, ... con el tema por defecto


# --------------------------------------------------------------------------- #
# Fuente monoespaciada
# --------------------------------------------------------------------------- #
FONT_CANDIDATES = [
    "JetBrains Mono", "Cascadia Code", "Cascadia Mono", "Fira Code",
    "Source Code Pro", "DejaVu Sans Mono", "Menlo", "Consolas",
    "Liberation Mono", "Courier New",
]
FONT_SIZE = 11


def get_mono_font(size: int = FONT_SIZE):
    from PySide6.QtGui import QFont, QFontDatabase
    available = set(QFontDatabase.families())
    family = next((f for f in FONT_CANDIDATES if f in available), None)
    font = QFont(family) if family else QFont()
    font.setStyleHint(QFont.Monospace)
    if not family:
        font.setFamily("monospace")
    font.setPointSize(size)
    font.setFixedPitch(True)
    return font


# --------------------------------------------------------------------------- #
# Hoja de estilos del tema activo
# --------------------------------------------------------------------------- #
def build_qss() -> str:
    t = THEMES[current_theme]
    return f"""
    QWidget {{
        background: {t['BG']};
        color: {t['FG']};
        selection-background-color: {t['SELECTION']};
        selection-color: {t['FG_BRIGHT']};
    }}
    QMainWindow, QDialog {{ background: {t['BG']}; }}

    QFrame#panel, QWidget#panel {{
        background: {t['PANEL']}; border: 1px solid {t['BORDER']}; border-radius: 4px;
    }}
    QLabel#banner {{ color: {t['FG_BRIGHT']}; }}
    QLabel#title  {{ color: {t['FG_BRIGHT']}; font-weight: bold; }}
    QLabel#prompt {{ color: {t['FG']}; }}
    QLabel#section {{ color: {t['FG_DIM']}; }}

    QPlainTextEdit, QTextBrowser, QTextEdit, QLineEdit {{
        background: {t['BG_ALT']}; color: {t['FG']};
        border: 1px solid {t['BORDER']}; border-radius: 4px; padding: 4px;
    }}

    QPushButton {{
        background: {t['PANEL']}; color: {t['FG_BRIGHT']};
        border: 1px solid {t['BORDER']}; border-radius: 4px; padding: 6px 12px;
    }}
    QPushButton:hover  {{ border-color: {t['FG_DIM']}; background: {t['BG_ALT']}; }}
    QPushButton:pressed {{ background: {t['SELECTION']}; }}
    QPushButton:disabled {{ color: {t['FG_DIM']}; border-color: {t['BORDER']}; }}
    QPushButton#primary {{ color: {t['BG']}; background: {t['OK']}; border: 1px solid {t['OK']}; font-weight: bold; }}
    QPushButton#primary:hover {{ background: {t['FG_BRIGHT']}; }}
    QPushButton#primary:disabled {{ color: {t['BG']}; background: {t['FG_DIM']}; border-color: {t['FG_DIM']}; }}

    QTreeWidget, QListWidget {{
        background: {t['BG_ALT']}; border: 1px solid {t['BORDER']}; border-radius: 4px; outline: 0;
    }}
    QTreeWidget::item {{ padding: 4px 2px; }}
    QTreeWidget::item:selected {{ background: {t['SELECTION']}; color: {t['FG_BRIGHT']}; }}
    QTreeWidget::item:hover {{ background: {t['CURRENT_LINE']}; }}

    QTabWidget::pane {{ border: 1px solid {t['BORDER']}; border-radius: 4px; top: -1px; }}
    QTabBar::tab {{
        background: {t['PANEL']}; color: {t['FG_DIM']}; border: 1px solid {t['BORDER']};
        padding: 6px 16px; margin-right: 2px;
        border-top-left-radius: 4px; border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{ color: {t['FG_BRIGHT']}; background: {t['BG_ALT']}; border-bottom-color: {t['BG_ALT']}; }}
    QTabBar::tab:hover {{ color: {t['FG']}; }}

    QMenuBar {{ background: {t['BG']}; color: {t['FG']}; }}
    QMenuBar::item:selected {{ background: {t['SELECTION']}; color: {t['FG_BRIGHT']}; }}
    QMenu {{ background: {t['BG_ALT']}; color: {t['FG']}; border: 1px solid {t['BORDER']}; }}
    QMenu::item:selected {{ background: {t['SELECTION']}; color: {t['FG_BRIGHT']}; }}

    QStatusBar {{ background: {t['PANEL']}; color: {t['FG_DIM']}; border-top: 1px solid {t['BORDER']}; }}

    QSplitter::handle {{ background: {t['BORDER']}; }}
    QSplitter::handle:hover {{ background: {t['FG_DIM']}; }}

    QScrollBar:vertical {{ background: {t['BG']}; width: 12px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: {t['BORDER']}; min-height: 24px; border-radius: 6px; }}
    QScrollBar::handle:vertical:hover {{ background: {t['FG_DIM']}; }}
    QScrollBar:horizontal {{ background: {t['BG']}; height: 12px; margin: 0; }}
    QScrollBar::handle:horizontal {{ background: {t['BORDER']}; min-width: 24px; border-radius: 6px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

    QToolTip {{ background: {t['BG_ALT']}; color: {t['FG_BRIGHT']}; border: 1px solid {t['FG_DIM']}; }}

    QProgressBar {{
        background: {t['BG_ALT']}; border: 1px solid {t['BORDER']}; border-radius: 4px;
        text-align: center; color: {t['FG_BRIGHT']}; min-height: 16px; max-height: 18px;
    }}
    QProgressBar::chunk {{ background: {t['OK']}; border-radius: 3px; }}

    /* botones de opción (examen): indicador propio, visible también deshabilitado */
    QRadioButton::indicator {{
        width: 12px; height: 12px; border-radius: 7px;
        border: 1px solid {t['FG_DIM']}; background: {t['BG']};
    }}
    QRadioButton::indicator:hover {{ border-color: {t['FG_BRIGHT']}; }}
    QRadioButton::indicator:checked {{ background: {t['FG_BRIGHT']}; border-color: {t['FG_BRIGHT']}; }}
    QRadioButton::indicator:disabled {{ border-color: {t['BORDER']}; }}
    QRadioButton::indicator:checked:disabled {{ background: {t['FG']}; border-color: {t['FG']}; }}

    /* examen corregido: propiedad dinámica "exam" = ok | bad (ver widgets/quiz.py) */
    QRadioButton[exam="ok"] {{ color: {t['OK']}; font-weight: bold; }}
    QRadioButton[exam="bad"] {{ color: {t['ERROR']}; }}
    """

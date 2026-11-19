"""
theory_view.py — render de la teoría (bloques -> HTML estilizado).
theory_view.py — theory renderer (blocks -> styled HTML).
"""
from __future__ import annotations

import html
import re

from PySide6.QtWidgets import QTextBrowser

from .. import theme


def _text_of(value) -> str:
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value)


def _inline(value: str) -> str:
    """Escapa HTML y aplica `código` y **negrita** en línea."""
    s = html.escape(_text_of(value))
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    return s


class TheoryView(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        self.setFont(theme.get_mono_font())
        self.document().setDefaultStyleSheet(self._css())

    def _css(self) -> str:
        return f"""
        h2 {{ color: {theme.FG_BRIGHT}; }}
        p  {{ color: {theme.FG}; line-height: 150%; }}
        b  {{ color: {theme.FG_BRIGHT}; }}
        code {{ color: {theme.SYN_STR}; background: {theme.BG}; }}
        pre.code {{
            color: {theme.FG_BRIGHT}; background: {theme.BG};
            border: 1px solid {theme.BORDER}; padding: 8px;
        }}
        pre.out {{
            color: {theme.FG_DIM}; background: {theme.GUTTER_BG};
            border: 1px dashed {theme.BORDER}; padding: 8px;
        }}
        div.note {{
            color: {theme.WARN}; background: {theme.BG};
            border-left: 3px solid {theme.WARN}; padding: 6px 8px;
        }}
        """

    def apply_css(self) -> None:
        """Re-aplica la hoja de estilos (al cambiar de tema)."""
        self.document().setDefaultStyleSheet(self._css())

    def render_blocks(self, blocks: list[dict]) -> None:
        parts: list[str] = []
        for b in blocks:
            btype = b.get("type", "text")
            value = b.get("value", "")
            if btype == "heading":
                parts.append(f"<h2>{html.escape(_text_of(value))}</h2>")
            elif btype == "code":
                parts.append(f"<pre class='code'>{html.escape(_text_of(value))}</pre>")
            elif btype == "output":
                parts.append(f"<pre class='out'>{html.escape(_text_of(value))}</pre>")
            elif btype == "note":
                parts.append(f"<div class='note'>{_inline(value)}</div>")
            else:  # text
                parts.append(f"<p>{_inline(value)}</p>")
        self.setHtml("\n".join(parts))
        self.verticalScrollBar().setValue(0)

"""
quiz.py — examen final de autoevaluación (bilingüe), con preguntas y opciones
barajadas en cada intento. quiz.py — final self-assessment exam (bilingual),
shuffling questions and options on each attempt.

Al corregir, cada pregunta muestra si se acertó y, si no, cuál era la respuesta
correcta; "Nuevo intento" vuelve a barajar.
"""
from __future__ import annotations

import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QDialog, QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QScrollArea, QVBoxLayout, QWidget,
)

from .. import content as content_mod
from .. import theme


def _preparar(preguntas, lang, rng=None):
    """Baraja preguntas y opciones; recalcula el índice de la respuesta correcta.

    Devuelve una lista de items {texto, opciones, correcta} lista para mostrar.
    """
    rng = rng or random.Random()
    orden = list(range(len(preguntas)))
    rng.shuffle(orden)
    items = []
    for qi in orden:
        q = preguntas[qi]
        ops = list(enumerate(q["opciones"][lang]))  # (índice_original, texto)
        rng.shuffle(ops)
        correcta = next(k for k, (oi, _) in enumerate(ops) if oi == q["correcta"])
        items.append({
            "texto": q["q"][lang],
            "opciones": [txt for _, txt in ops],
            "correcta": correcta,
        })
    return items


class ExamDialog(QDialog):
    def __init__(self, i18n, progress: dict, parent=None, rng=None):
        super().__init__(parent)
        self.i18n = i18n
        self.progress = progress
        self._rng = rng
        self.setWindowTitle(i18n.t("exam_title"))
        self.resize(680, 640)

        data = content_mod.load_exam()
        self.pass_ratio = data.get("pass", 0.8)
        self._preguntas = data.get("questions", [])
        self.items: list[dict] = []
        self.grupos: list[QButtonGroup] = []
        self.cajas: list[QGroupBox] = []
        self.corregido = False

        root = QVBoxLayout(self)
        intro = QLabel(i18n.t("exam_intro"))
        intro.setWordWrap(True)
        root.addWidget(intro)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        root.addWidget(self.scroll, 1)

        self.resultado = QLabel("")
        self.resultado.setObjectName("section")
        self.resultado.setWordWrap(True)
        root.addWidget(self.resultado)

        fila = QHBoxLayout()
        self.btn = QPushButton(i18n.t("exam_check"))
        self.btn.setObjectName("primary")
        self.btn.clicked.connect(self._on_button)
        fila.addWidget(self.btn)
        fila.addStretch(1)
        root.addLayout(fila)

        self._nuevo_intento()

    # ------------------------------------------------------------------ #
    def _nuevo_intento(self) -> None:
        """(Re)construye el examen con preguntas y opciones barajadas."""
        self.items = _preparar(self._preguntas, self.i18n.lang, self._rng)
        self.grupos, self.cajas = [], []
        cont = QWidget()
        v = QVBoxLayout(cont)
        for i, it in enumerate(self.items, 1):
            caja = QGroupBox(f"{i}. {it['texto']}")
            cv = QVBoxLayout(caja)
            grupo = QButtonGroup(caja)
            for j, op in enumerate(it["opciones"]):
                rb = QRadioButton(op)
                grupo.addButton(rb, j)
                cv.addWidget(rb)
            self.grupos.append(grupo)
            self.cajas.append(caja)
            v.addWidget(caja)
        v.addStretch(1)
        self.scroll.setWidget(cont)  # el contenido anterior se destruye
        self.corregido = False
        self.resultado.setText("")
        self.btn.setText(self.i18n.t("exam_check"))

    def _on_button(self) -> None:
        if self.corregido:
            self._nuevo_intento()
        else:
            self.corregir()

    def corregir(self) -> None:
        total = len(self.items)
        aciertos = 0
        for i, (grupo, caja, it) in enumerate(zip(self.grupos, self.cajas, self.items), 1):
            elegida = grupo.checkedId()
            bien = elegida == it["correcta"]
            aciertos += bien
            for j, b in enumerate(grupo.buttons()):
                b.setEnabled(False)
                # la correcta en verde; la elegida por error, en rojo (reglas en theme.build_qss;
                # un setStyleSheet propio haría desaparecer el círculo del botón)
                marca = "ok" if j == it["correcta"] else "bad" if j == elegida else ""
                if marca:
                    b.setProperty("exam", marca)
                    b.style().unpolish(b)
                    b.style().polish(b)
            caja.setTitle(f"{'✓' if bien else '✗'} {i}. {it['texto']}")
            caja.setStyleSheet(f"QGroupBox {{ border-color: {theme.OK if bien else theme.ERROR}; }}"
                               f"QGroupBox::title {{ color: {theme.OK if bien else theme.ERROR}; }}")
            if not bien:
                texto = self.i18n.t("exam_correct_answer").format(a=it["opciones"][it["correcta"]])
                if elegida < 0:
                    texto = f"{self.i18n.t('exam_unanswered')} {texto}"
                nota = QLabel(texto)
                nota.setTextFormat(Qt.PlainText)  # las opciones pueden llevar < > de código
                nota.setObjectName("exam_feedback")
                nota.setWordWrap(True)
                nota.setStyleSheet(f"color: {theme.OK};")
                caja.layout().addWidget(nota)

        pct = round(aciertos * 100 / total) if total else 0
        aprobado = bool(total) and aciertos >= self.pass_ratio * total
        self.progress["exam_score"] = pct
        if aprobado:
            self.progress["exam_passed"] = True
        msg = self.i18n.t("exam_result").format(a=aciertos, t=total, p=pct)
        if aprobado:
            msg += "  " + self.i18n.t("exam_passed_msg")
        else:
            msg += "  " + self.i18n.t("exam_failed_msg").format(n=int(self.pass_ratio * 100))
        self.resultado.setText(msg)
        self.corregido = True
        self.btn.setText(self.i18n.t("exam_retry"))
        self.scroll.verticalScrollBar().setValue(0)

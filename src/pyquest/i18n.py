"""
i18n.py — cadenas de la interfaz en español e inglés.
i18n.py — UI strings in Spanish and English.

El contenido didáctico (teoría/ejercicios) lleva sus propias traducciones
dentro de los archivos JSON; aquí solo están los textos de la interfaz.
"""
from __future__ import annotations

LANGUAGES = ("es", "en")

STRINGS: dict[str, dict[str, str]] = {
    "app_title":        {"es": "PyQuest — Aprende Python",      "en": "PyQuest — Learn Python"},
    "tab_theory":       {"es": "Teoría",                        "en": "Theory"},
    "tab_practice":     {"es": "Práctica",                      "en": "Practice"},
    "btn_run":          {"es": "▶ Ejecutar",                    "en": "▶ Run"},
    "btn_check":        {"es": "✓ Comprobar",                   "en": "✓ Check"},
    "btn_hint":         {"es": "Pista",                         "en": "Hint"},
    "btn_solution":     {"es": "Ver solución",                  "en": "Show solution"},
    "btn_reset":        {"es": "↺ Reiniciar",                   "en": "↺ Reset"},
    "btn_stop":         {"es": "■ Detener",                     "en": "■ Stop"},
    "input_placeholder": {"es": "Escribe aquí y pulsa Enter cuando el programa pida datos…",
                          "en": "Type here and press Enter when the program asks for input…"},
    "process_ended":    {"es": "proceso terminado",            "en": "process ended"},
    "console_title":    {"es": "// Salida",                     "en": "// Output"},
    "prompt_label":     {"es": "Enunciado",                     "en": "Task"},
    "menu_view":        {"es": "Ver",                           "en": "View"},
    "menu_help":        {"es": "Ayuda",                         "en": "Help"},
    "menu_file":        {"es": "Archivo",                       "en": "File"},
    "menu_lang":        {"es": "Idioma",                        "en": "Language"},
    "menu_theme":       {"es": "Tema",                          "en": "Theme"},
    "theme_green":      {"es": "Verde fósforo",                 "en": "Green phosphor"},
    "theme_amber":      {"es": "Ámbar",                         "en": "Amber"},
    "theme_dos":        {"es": "MS-DOS azul",                   "en": "MS-DOS blue"},
    "theme_light":      {"es": "Claro",                        "en": "Light"},
    "search_placeholder": {"es": "Buscar lección o teoría…",    "en": "Search lesson or theory…"},
    "menu_zoom_in":     {"es": "Aumentar fuente",              "en": "Increase font"},
    "menu_zoom_out":    {"es": "Reducir fuente",               "en": "Decrease font"},
    "menu_zoom_reset":  {"es": "Tamaño normal",                "en": "Normal size"},
    "toggle_scanlines": {"es": "Líneas de escaneo (CRT)",       "en": "Scanlines (CRT)"},
    "lang_es":          {"es": "Español",                       "en": "Spanish"},
    "lang_en":          {"es": "Inglés",                        "en": "English"},
    "menu_about":       {"es": "Acerca de",                     "en": "About"},
    "menu_exit":        {"es": "Salir",                         "en": "Exit"},
    "menu_reset_progress": {"es": "Reiniciar progreso",         "en": "Reset progress"},
    "confirm_reset":    {"es": "¿Seguro que quieres borrar todo tu progreso?",
                         "en": "Are you sure you want to erase all your progress?"},
    "running":          {"es": "Ejecutando…",                   "en": "Running…"},
    "checking":         {"es": "Comprobando…",                  "en": "Checking…"},
    "all_passed":       {"es": "¡Correcto! Todos los tests pasan.", "en": "Correct! All tests pass."},
    "some_failed":      {"es": "Aún no. Revisa los fallos:",     "en": "Not yet. Check the failures:"},
    "syntax_blocked":   {"es": "Hay errores de sintaxis; corrígelos antes de comprobar.",
                         "en": "There are syntax errors; fix them before checking."},
    "timed_out":        {"es": "Tiempo agotado: ¿hay un bucle infinito?",
                         "en": "Timed out: is there an infinite loop?"},
    "static_warnings":  {"es": "Avisos del analizador:",        "en": "Analyzer warnings:"},
    "lesson_done":      {"es": "Lección completada ✔",          "en": "Lesson completed ✔"},
    "exercise_done":    {"es": "Ejercicio resuelto ✔",          "en": "Exercise solved ✔"},
    "no_lesson":        {"es": "Selecciona una lección en el panel de la izquierda.",
                         "en": "Select a lesson from the left panel."},
    "ready":            {"es": "Listo.",                        "en": "Ready."},
    "exercise_n":       {"es": "Ejercicio",                     "en": "Exercise"},
    "of":               {"es": "de",                            "en": "of"},
    "progress":         {"es": "Progreso",                      "en": "Progress"},
    "xp":               {"es": "XP",                            "en": "XP"},
    "streak":           {"es": "Racha",                         "en": "Streak"},
    "days":             {"es": "días",                          "en": "days"},
    "achievement":      {"es": "Logro",                         "en": "Achievement"},
    "confirm_solution": {"es": "Esto reemplazará tu código por la solución. ¿Continuar?",
                         "en": "This will replace your code with the solution. Continue?"},
    "confirm_solution_xp": {"es": "Esto reemplazará tu código por la solución y este ejercicio "
                                  "ya no dará XP al resolverlo. ¿Continuar?",
                            "en": "This will replace your code with the solution and this exercise "
                                  "will no longer give XP when solved. Continue?"},
    "no_xp_solution":   {"es": "Resuelto tras ver la solución: sin XP esta vez.",
                         "en": "Solved after viewing the solution: no XP this time."},
    "draft_restored":   {"es": "(borrador recuperado: es el código que dejaste a medias)",
                         "en": "(draft restored: the code you left unfinished)"},
    "exam_correct_answer": {"es": "Respuesta correcta: {a}",  "en": "Correct answer: {a}"},
    "exam_unanswered":  {"es": "(sin responder)",              "en": "(not answered)"},
    "exam_retry":       {"es": "↻ Nuevo intento",              "en": "↻ New attempt"},
    "line":             {"es": "línea",                         "en": "line"},
    "menu_achievements": {"es": "Logros",                       "en": "Achievements"},
    "menu_playground":  {"es": "Playground",                    "en": "Playground"},
    "playground_title": {"es": "Playground — zona libre",       "en": "Playground — free coding"},
    "btn_clear":        {"es": "Limpiar",                       "en": "Clear"},
    "menu_stats":       {"es": "Mi progreso",                    "en": "My progress"},
    "stats_title":      {"es": "Mi progreso",                    "en": "My progress"},
    "menu_next":        {"es": "Siguiente pendiente",            "en": "Next pending"},
    "all_done":         {"es": "¡Has completado todos los ejercicios!", "en": "You've completed all exercises!"},
    "menu_shortcuts":   {"es": "Atajos de teclado",              "en": "Keyboard shortcuts"},
    "menu_export":      {"es": "Exportar progreso…",             "en": "Export progress…"},
    "menu_import":      {"es": "Importar progreso…",             "en": "Import progress…"},
    "export_ok":        {"es": "Progreso exportado.",            "en": "Progress exported."},
    "import_ok":        {"es": "Progreso importado.",            "en": "Progress imported."},
    "import_err":       {"es": "No se pudo importar el progreso.","en": "Could not import progress."},
    "menu_review":      {"es": "Repasar fallados",              "en": "Review mistakes"},
    "nothing_to_review":{"es": "No hay ejercicios con fallos para repasar.", "en": "No mistakes to review."},
    "stats_fails":      {"es": "Ejercicios con fallos",          "en": "Exercises with mistakes"},
    "menu_bookmark":    {"es": "Marcar/desmarcar lección",      "en": "Toggle bookmark"},
    "bookmarked":       {"es": "Lección marcada ★",             "en": "Lesson bookmarked ★"},
    "unbookmarked":     {"es": "Marcador quitado",              "en": "Bookmark removed"},
    "hint_n":           {"es": "Pista",                         "en": "Hint"},
    "hint_last":        {"es": "Era la última pista. Si te atascas, prueba 'Ver solución'.", "en": "That was the last hint. If stuck, try 'Show solution'."},
    "hint_no_more":     {"es": "No hay más pistas.",            "en": "No more hints."},
    "menu_course":      {"es": "Curso",                        "en": "Course"},
    "menu_exam":        {"es": "Examen final",                 "en": "Final exam"},
    "exam_title":       {"es": "Examen final",                 "en": "Final exam"},
    "exam_intro":       {"es": "Marca una respuesta por pregunta y pulsa Corregir.", "en": "Pick one answer per question and press Check."},
    "exam_check":       {"es": "✓ Corregir",                   "en": "✓ Check"},
    "exam_result":      {"es": "Aciertos: {a}/{t} ({p}%).",    "en": "Correct: {a}/{t} ({p}%)."},
    "exam_passed_msg":  {"es": "¡Aprobado! Enhorabuena, dominas lo esencial.", "en": "Passed! Well done, you've got the essentials."},
    "exam_failed_msg":  {"es": "Necesitas al menos {n}% para aprobar.", "en": "You need at least {n}% to pass."},
}


class I18N:
    """Pequeño contenedor de idioma + función de traducción ``t``."""

    def __init__(self, lang: str = "es") -> None:
        self.lang = lang if lang in LANGUAGES else "es"

    def set_language(self, lang: str) -> None:
        if lang in LANGUAGES:
            self.lang = lang

    def t(self, key: str) -> str:
        entry = STRINGS.get(key)
        if not entry:
            return key
        return entry.get(self.lang, entry.get("es", key))

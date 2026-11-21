"""Lógica de puntaje por palabras clave (modo gratuito, sin LLM).

Es el fallback cuando no hay API key de Groq. Es una heurística simple: cuenta
cuántas palabras clave esperadas aparecen en la transcripción del estudiante.
"""

from __future__ import annotations

from typing import List, Tuple


def score_keywords(transcript: str, keywords: List[str]) -> Tuple[int, int]:
    """Devuelve (aciertos, total) de palabras clave encontradas en la respuesta.

    La comparación es insensible a mayúsculas y normaliza el texto.
    """
    if not transcript:
        return 0, len(keywords)
    text = " ".join(transcript.lower().split())
    matched = [kw for kw in keywords if kw.lower() in text]
    return len(matched), len(keywords)


def coverage_to_grade(aciertos: int, total: int) -> int:
    """Convierte la cobertura de palabras clave a una nota 0–100 (heurística)."""
    if total == 0:
        return 0
    return round((aciertos / total) * 100)


def grade_band(nota: int) -> Tuple[str, str]:
    """Devuelve (emoji, color) según la nota, para la interfaz."""
    if nota >= 80:
        return "🎉", "green"
    if nota >= 60:
        return "👍", "blue"
    if nota >= 40:
        return "🤔", "orange"
    return "😟", "red"


def generar_mensaje(nombre: str, puntaje: int, total: int) -> str:
    """Genera el mensaje de cierre para el estudiante (y para el avatar)."""
    if total > 0 and puntaje / total >= 0.8:
        return (
            f"¡Hola {nombre}! Felicidades, obtuviste {puntaje} de {total} en tu "
            "evaluación de Python. ¡Gran trabajo!"
        )
    return (
        f"Hola {nombre}, tu puntaje fue {puntaje} de {total}. Te animo a repasar "
        "algunos temas y volver a intentarlo. ¡Tú puedes!"
    )

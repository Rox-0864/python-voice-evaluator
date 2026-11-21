"""Lógica del modo examen: selección de preguntas y resumen final.

En el modo examen el feedback se oculta durante la prueba (solo se registra el
puntaje) y se muestra un resumen al final. La unidad es el estudiante, no la
pregunta.
"""

from __future__ import annotations

import random
from typing import List, Optional


def select_questions(
    questions: List[dict],
    n: int,
    categoria: Optional[str] = None,
    seed: Optional[int] = None,
) -> List[dict]:
    """Selecciona ``n`` preguntas (aleatorias, opcionalmente de una categoría).

    Si ``n`` supera el tamaño del conjunto, devuelve todas las disponibles.
    """
    pool = [q for q in questions if categoria is None or q.get("categoria") == categoria]
    if n >= len(pool):
        return pool
    rng = random.Random(seed)
    return rng.sample(pool, n)


def summarize_exam(respuestas: List[dict]) -> dict:
    """Resumen del examen: cantidad, puntaje promedio y aprobado/reprobado.

    ``respuestas`` es una lista de dicts con al menos la clave ``puntaje``
    (0–100). Se aprueba con promedio >= 60.
    """
    if not respuestas:
        return {"n": 0, "promedio": 0, "aprobado": False}

    n = len(respuestas)
    promedio = round(sum(r["puntaje"] for r in respuestas) / n)
    return {"n": n, "promedio": promedio, "aprobado": promedio >= 60}

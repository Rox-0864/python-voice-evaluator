"""Carga y validación del banco de preguntas (JSON)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional


def load_questions(path) -> List[dict]:
    """Carga las preguntas desde un archivo JSON."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate_questions(questions: List[dict]) -> List[str]:
    """Devuelve una lista de problemas (vacía si el banco es válido).

    Cada pregunta debe tener ``pregunta``, ``palabras_clave`` y ``contexto_ideal``.
    """
    problems: List[str] = []
    for q in questions:
        qid = q.get("id", "?")
        for field in ("pregunta", "palabras_clave", "contexto_ideal"):
            if field not in q or not q[field]:
                problems.append(f"Pregunta '{qid}': falta el campo '{field}'")
        if not isinstance(q.get("palabras_clave"), list) or not q.get("palabras_clave"):
            problems.append(f"Pregunta '{qid}': 'palabras_clave' debe ser una lista no vacía")
    return problems


def categories(questions: List[dict]) -> List[str]:
    """Devuelve las categorías únicas, en orden de aparición."""
    seen, out = set(), []
    for q in questions:
        c = q.get("categoria", "General")
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def filter_by_category(questions: List[dict], categoria: Optional[str]) -> List[dict]:
    """Filtra por categoría; ``None`` devuelve todas."""
    if not categoria:
        return questions
    return [q for q in questions if q.get("categoria") == categoria]

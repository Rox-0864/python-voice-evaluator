"""Evaluación semántica con un LLM (Groq).

Compara la respuesta del estudiante con la pregunta y su contexto ideal, y
devuelve un feedback motivador + una calificación 0–100 según una rúbrica.
"""

from __future__ import annotations

import json
import re
from typing import Optional

SYSTEM_PROMPT = """Eres un instructor experto, empático y motivador de Python.
Tu tarea es evaluar la respuesta oral de un estudiante a una pregunta técnica.

Recibirás la pregunta, el contexto de respuesta ideal y la respuesta del estudiante.
Devuelve UNICAMENTE un objeto JSON con esta estructura:
{
  "feedback": "tu retroalimentación motivadora y específica, en español",
  "calificacion": <número entero entre 0 y 100>
}

Rúbrica para `calificacion`:
- 80-100: cubre todos los puntos clave del contexto ideal (excelente).
- 60-79: cubre la mayoría, le falta algún detalle (bien).
- 40-59: cubre la mitad o es superficial (suficiente).
- 20-39: se acerca al tema pero es mayormente incorrecto (insuficiente).
- 0-19: muy alejado de lo esperado (muy deficiente).

El `feedback` debe ser específico: explica qué le faltó o qué hizo bien,
comparando con el contexto ideal. Usa un tono humano y cercano.
No incluyas ningún texto fuera del JSON."""


def evaluar_con_llm(pregunta: str, contexto_ideal: str, respuesta: str,
                    api_key: str, model: str = "llama3-8b-8192") -> Optional[dict]:
    """Evalúa la respuesta y devuelve {'feedback': str, 'calificacion': int}."""
    from groq import Groq

    user = (
        f"Pregunta del instructor: {pregunta}\n"
        f"Contexto de respuesta ideal: {contexto_ideal}\n"
        f"Respuesta del estudiante: {respuesta}"
    )

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        content = completion.choices[0].message.content
        return _parse_evaluacion(content)
    except Exception:
        return None


def _parse_evaluacion(content: str) -> Optional[dict]:
    """Parsea la salida del LLM a un dict, con tolerancia a JSON sucio."""
    if not content:
        return None

    # 1) Intento directo de json.loads (sobre el bloque JSON).
    try:
        data = json.loads(content)
        return _sanitize(data)
    except json.JSONDecodeError:
        pass

    # 2) Extraer el primer objeto JSON con regex.
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            return _sanitize(json.loads(match.group(0)))
        except json.JSONDecodeError:
            pass

    # 3) Último recurso: extraer feedback y calificación con regex.
    cal = re.search(r"calificacion[\"']?\s*[:=]\s*(\d{1,3})", content)
    feedback = re.search(r"feedback[\"']?\s*[:=]\s*[\"'](.+?)[\"']", content, re.DOTALL)
    if cal:
        return {
            "feedback": feedback.group(1) if feedback else content.strip(),
            "calificacion": max(0, min(100, int(cal.group(1)))),
        }
    return None


def _sanitize(data: dict) -> Optional[dict]:
    """Normaliza las claves y valida los campos esperados."""
    feedback = data.get("feedback") or data.get("instructor_respuesta")
    cal = data.get("calificacion") or data.get("nota")
    if feedback is None:
        return None
    try:
        calificacion = max(0, min(100, int(cal)))
    except (TypeError, ValueError):
        calificacion = 0
    return {"feedback": str(feedback), "calificacion": calificacion}

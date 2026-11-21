"""Carga de preguntas desde Firebase/Firestore (alternativa al JSON local).

Replica la funcionalidad del `evaluacion.py` original, pero con las credenciales
leídas desde secretos (nunca hardcodeadas) y normalizando la estructura de
Firestore al mismo formato que el banco local (`data/preguntas.json`).
"""

from __future__ import annotations

import json
from typing import List, Optional


def init_firestore(service_account):
    """Inicializa Firebase y devuelve un cliente Firestore.

    Args:
        service_account: puede ser un dict con credenciales, una cadena JSON
        (contenido del archivo de cuenta de servicio) o una ruta a un archivo.
    """
    import firebase_admin
    from firebase_admin import credentials, firestore

    if isinstance(service_account, str):
        text = service_account.strip()
        if text.startswith("{"):
            cred = credentials.Certificate(json.loads(text))
        else:
            cred = credentials.Certificate(text)  # ruta al archivo JSON
    else:
        cred = credentials.Certificate(service_account)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    return firestore.client()


def load_questions_from_firestore(db, curso_id: str) -> List[dict]:
    """Carga las preguntas de un curso desde Firestore.

    Estructura esperada en Firestore (colección ``cursos``):

        cursos/<curso_id> -> {
          "titulo": "Curso de Python",
          "capitulos": {
            "cap_01": {
              "titulo": "Fundamentos",
              "evaluacion": {
                "instructor_pregunta": "¿...?",
                "contexto_respuesta": "respuesta ideal...",
                "palabras_clave": ["print", "consola"]  # opcional
              }
            },
            ...
          }
        }

    Devuelve una lista de preguntas normalizadas al formato del banco local.
    """
    doc = db.collection("cursos").document(curso_id).get()
    curso = doc.to_dict()
    if not curso or "capitulos" not in curso:
        return []

    preguntas: List[dict] = []
    for nombre_capitulo, datos in sorted(curso["capitulos"].items()):
        ev = datos.get("evaluacion") or {}
        if not (ev.get("instructor_pregunta") and ev.get("contexto_respuesta")):
            continue
        preguntas.append(
            {
                "id": f"fb-{nombre_capitulo}",
                "categoria": datos.get("titulo")
                or nombre_capitulo.replace("_", " ").title(),
                "dificultad": ev.get("dificultad", "basico"),
                "pregunta": ev["instructor_pregunta"],
                "palabras_clave": ev.get("palabras_clave", []),
                "contexto_ideal": ev["contexto_respuesta"],
            }
        )
    return preguntas

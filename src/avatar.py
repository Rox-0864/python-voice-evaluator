"""Generación de un avatar animado que "habla" el feedback (D-ID, opcional).

Requiere DID_API_KEY. Si no hay clave o falla, la app simplemente omite el avatar.
"""

from __future__ import annotations

import time
from typing import Optional

import requests

SOURCE_URL = "https://create-images-results.d-id.com/DefaultFriendlyTutor.png"
VOICE_ID = "es-ES-Neural2-B"


def generar_video(api_key: str, mensaje: str) -> Optional[str]:
    """Genera el video del avatar y devuelve su URL, o None si falla."""
    if not api_key:
        return None

    url = "https://api.d-id.com/talks"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "script": {
            "type": "text",
            "input": mensaje,
            "provider": {"type": "google", "voice_id": VOICE_ID},
        },
        "source_url": SOURCE_URL,
        "driver_url": "bank://lively",
        "config": {"fluent": True},
    }

    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        talk_id = resp.json()["id"]

        # Polling (máx ~20 s) hasta que el video esté listo.
        for _ in range(10):
            check = requests.get(f"https://api.d-id.com/talks/{talk_id}",
                                 headers=headers, timeout=30)
            if check.status_code == 200 and check.json().get("status") == "done":
                return check.json().get("result_url")
            time.sleep(2)
        return None
    except Exception:
        return None

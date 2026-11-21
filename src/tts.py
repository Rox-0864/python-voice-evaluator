"""Síntesis de voz (TTS) con múltiples proveedores.

- ``elevenlabs``: voces naturales (pago, ELEVENLABS_API_KEY).
- ``openai``: API TTS de OpenAI (pago, OPENAI_API_KEY).
- ``gtts``: Google Text-to-Speech (gratuito, sin API key).

Todas devuelven ``bytes | None``: el contenido del audio MP3, o ``None`` ante error.
"""

from __future__ import annotations

from typing import Optional


def text_to_speech(text: str, provider: str, api_key: str = "",
                   voice_id: str = "l1zE9xgNpUTaQCZzpNJa") -> Optional[bytes]:
    """Convierte texto a audio según el proveedor indicado."""
    if provider == "elevenlabs":
        return tts_elevenlabs(text, api_key, voice_id)
    if provider == "openai":
        return tts_openai(text, api_key)
    return tts_gtts(text)


def tts_elevenlabs(text: str, api_key: str, voice_id: str) -> Optional[bytes]:
    import requests

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json",
               "xi-api-key": api_key}
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


def tts_openai(text: str, api_key: str) -> Optional[bytes]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    try:
        resp = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
        return resp.read()
    except Exception:
        return None


def tts_gtts(text: str) -> Optional[bytes]:
    from gtts import gTTS

    try:
        tts = gTTS(text=text, lang="es")
        import io as _io

        buf = _io.BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None

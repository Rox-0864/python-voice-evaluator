"""Reconocimiento de voz (STT) con múltiples proveedores.

- ``groq``: Whisper-large-v3 (pago, requiere GROQ_API_KEY).
- ``assemblyai``: API de AssemblyAI (pago).
- ``google``: reconocimiento gratuito vía SpeechRecognition (sin API key).

Todas devuelven ``str | None``: el texto transcrito, o ``None`` ante error.
"""

from __future__ import annotations

import io
import os
import tempfile
from typing import Optional


def transcribe(audio_bytes: bytes, provider: str, api_key: str = "",
               model: str = "whisper-large-v3") -> Optional[str]:
    """Transcribe audio según el proveedor indicado."""
    if provider == "groq":
        return transcribe_groq(audio_bytes, api_key, model)
    if provider == "assemblyai":
        return transcribe_assemblyai(audio_bytes, api_key)
    return transcribe_google(audio_bytes)


def transcribe_groq(audio_bytes: bytes, api_key: str, model: str) -> Optional[str]:
    from groq import Groq

    client = Groq(api_key=api_key)
    stream = io.BytesIO(audio_bytes)
    stream.name = "audio.wav"
    try:
        transcription = client.audio.transcriptions.create(file=stream, model=model)
        return transcription.text
    except Exception:
        return None


def transcribe_assemblyai(audio_bytes: bytes, api_key: str) -> Optional[str]:
    import assemblyai as aai

    aai.settings.api_key = api_key
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fh:
        fh.write(audio_bytes)
        path = fh.name
    try:
        transcriber = aai.Transcriber()
        config = aai.TranscriptionConfig(language_code="es")
        transcript = transcriber.transcribe(path, config=config)
        return transcript.text if transcript.status != aai.TranscriptStatus.error else None
    except Exception:
        return None
    finally:
        if os.path.exists(path):
            os.unlink(path)


def transcribe_google(audio_bytes: bytes) -> Optional[str]:
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fh:
        fh.write(audio_bytes)
        path = fh.name
    try:
        with sr.AudioFile(path) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language="es-ES")
    except Exception:
        return None
    finally:
        if os.path.exists(path):
            os.unlink(path)

"""Configuración central del evaluador oral de Python.

Consolida los tres repositorios originales en una sola app con proveedores
seleccionables. Cada proveedor tiene una variante gratuita (sin API key) para
que la app funcione sin costos.

Los secretos (API keys) se leen desde Streamlit secrets o variables de entorno,
nunca se hardcodean en el código (uno de los errores corregidos).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Rutas base
BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = BASE_DIR / "data" / "preguntas.json"
RESULTS_PATH = BASE_DIR / "data" / "resultados.json"


def get_secret(key: str, default: str = "") -> str:
    """Resuelve un secreto: Streamlit secrets -> env -> default.

    En Streamlit Cloud los secretos viven en ``.streamlit/secrets.toml``; en
    local, en variables de entorno (cargadas con ``python-dotenv``).
    """
    try:
        import streamlit as st

        if key in st.secrets:
            return st.secrets[key]
    except Exception:  # noqa: BLE001 - no hay secrets configurados
        pass
    return os.environ.get(key, default)


@dataclass
class Config:
    """Parámetros de la aplicación."""

    # Proveedores seleccionables (se resuelven según las API keys disponibles).
    stt_provider: str = "groq"        # "groq" | "assemblyai" | "google"
    tts_provider: str = "elevenlabs"  # "elevenlabs" | "openai" | "gtts"
    eval_mode: str = "llm"            # "llm" | "keywords" | "auto"

    # Modelos
    stt_model: str = "whisper-large-v3"
    llm_model: str = "llama3-8b-8192"
    tts_voice_id: str = "l1zE9xgNpUTaQCZzpNJa"

    # Rutas
    questions_path: Path = QUESTIONS_PATH
    results_path: Path = RESULTS_PATH

    def resolve(self) -> dict:
        """Devuelve los proveedores efectivos según las API keys disponibles.

        Regla: si no hay API key de un proveedor pago, se cae al gratuito.
        """
        has_groq = bool(get_secret("GROQ_API_KEY"))
        has_elevenlabs = bool(get_secret("ELEVENLABS_API_KEY"))
        has_openai = bool(get_secret("OPENAI_API_KEY"))
        has_assemblyai = bool(get_secret("ASSEMBLYAI_API_KEY"))
        has_did = bool(get_secret("DID_API_KEY"))

        stt = self.stt_provider
        if stt == "groq" and not has_groq:
            stt = "assemblyai" if has_assemblyai else "google"

        tts = self.tts_provider
        if tts == "elevenlabs" and not has_elevenlabs:
            tts = "openai" if has_openai else "gtts"

        mode = self.eval_mode
        if mode in ("llm", "auto") and not has_groq:
            mode = "keywords"

        return {
            "stt": stt,
            "tts": tts,
            "eval_mode": mode,
            "avatar_disponible": has_did,
        }

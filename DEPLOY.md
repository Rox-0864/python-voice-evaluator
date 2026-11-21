# Guía de despliegue — Python Voice Evaluator

Cómo desplegar la app en **Streamlit Community Cloud** (gratis) y configurar los
proveedores de IA.

---

## 1. Requisitos previos

- Cuenta en [GitHub](https://github.com) con este repositorio.
- Cuenta en [Streamlit Community Cloud](https://share.streamlit.io).
- (Opcional) API keys de los proveedores que quieras usar.

---

## 2. Desplegar en Streamlit Cloud

1. Entrá a [share.streamlit.io](https://share.streamlit.io) e iniciá sesión con GitHub.
2. Clic en **"Create app"** (o "New app").
3. Elegí el repositorio `python-voice-evaluator`, la rama `main` y el archivo
   **`app.py`** como *Main file path*.
4. Clic en **"Deploy"**.

Streamlit Cloud detecta automáticamente `requirements.txt` e instala las
dependencias. La app ya incluye el arranque de `sys.path` necesario para que los
imports de `src/` funcionen en la nube.

> **Sin configuración adicional, la app funciona en modo gratuito** (Google STT
> + gTTS + evaluación por palabras clave).

---

## 3. Configurar secretos (proveedores de IA)

En el dashboard de la app (`Settings → Secrets`), pegá las claves que quieras
usar. Usá `.streamlit/secrets.toml.example` como plantilla.

```toml
GROQ_API_KEY = "tu-clave"
ELEVENLABS_API_KEY = "tu-clave"
OPENAI_API_KEY = "tu-clave"
ASSEMBLYAI_API_KEY = "tu-clave"
DID_API_KEY = "tu-clave"
```

| Proveedor | Efecto al configurarla |
|-----------|------------------------|
| `GROQ_API_KEY` | STT con Whisper + evaluación semántica (rúbrica 0–100) |
| `ELEVENLABS_API_KEY` | Voz de alta calidad para el feedback |
| `OPENAI_API_KEY` | TTS alternativo |
| `ASSEMBLYAI_API_KEY` | STT alternativo |
| `DID_API_KEY` | Avatar animado |

---

## 4. Banco de preguntas desde Firebase (opcional)

Si querés servir las preguntas desde Firestore en lugar del JSON local:

1. Generá una **cuenta de servicio** en Firebase (`Project settings → Service
   accounts → Generate new private key`).
2. Pegá el contenido JSON como secreto:

```toml
FIREBASE_SERVICE_ACCOUNT = """{"type":"service_account","project_id":"...","private_key":"..."}"""
```

3. En `config.py`, seteá:

```python
question_source = "firebase"
firebase_course_id = "<id-del-documento-en-cursos>"
```

> La colección en Firestore es `cursos`; ver la estructura en el README.

---

## 5. Notas y limitaciones

- **El cronómetro del modo examen se actualiza con cada interacción.** Streamlit
  no refresca la página en tiempo real sin un componente externo; el tiempo se
  verifica al responder.
- Las APIs de voz (STT/TTS) requieren conexión a internet.
- Los resultados (`data/resultados.json`) persisten en el filesystem del
  despliegue; se reinician con cada redeploy.

---

## 6. Despliegue local (alternativa)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # completá las claves que quieras
streamlit run app.py
```

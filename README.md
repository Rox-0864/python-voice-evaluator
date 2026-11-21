# Python Voice Evaluator 🎓

Evaluador oral de Python que escucha la respuesta del estudiante, la evalúa
(con un LLM o por palabras clave) y entrega feedback por voz y, opcionalmente,
con un avatar animado. Incluye banco de preguntas, historial y exportación de
resultados.

Este repositorio **integra y amplía** tres proyectos anteriores:

- `evaluador_audio` → reconocimiento de voz (Groq Whisper) y evaluación con LLM.
- `Evaluador_interactivo` → banco de preguntas y herramientas gratuitas.
- `Evaluador-Stl-avatar` → avatar (D-ID) y exportación CSV/PDF.

Los errores corregidos durante la integración están en la **[guía de estudio](GUIA_DE_ESTUDIO.md)**.

---

## Características

- **Banco de preguntas** por categoría y dificultad (12 preguntas de ejemplo).
- **Reconocimiento de voz** con 3 proveedores (Groq, AssemblyAI, Google).
- **Evaluación** semántica con LLM (rúbrica 0–100) o por palabras clave.
- **Feedback por voz** con 3 proveedores de TTS (ElevenLabs, OpenAI, gTTS).
- **Avatar animado** opcional (D-ID) que "habla" el feedback.
- **Historial** de resultados + **exportación CSV y PDF**.
- **Funciona sin pagar**: sin API keys, usa Google STT + gTTS + evaluación por
  palabras clave.

---

## Estructura

```
python-voice-evaluator/
├── app.py                  # interfaz Streamlit
├── config.py               # configuración y resolución de proveedores
├── data/
│   └── preguntas.json      # banco de preguntas
├── src/
│   ├── questions.py        # carga y validación del banco
│   ├── firebase_store.py   # banco de preguntas desde Firestore (opcional)
│   ├── stt.py              # voz → texto (Groq/AssemblyAI/Google)
│   ├── tts.py              # texto → voz (ElevenLabs/OpenAI/gTTS)
│   ├── llm.py              # evaluación con LLM (Groq)
│   ├── evaluator.py        # puntaje por palabras clave
│   ├── avatar.py           # avatar D-ID
│   ├── export.py           # CSV/PDF
│   └── store.py            # persistencia del historial
├── .env.example            # plantilla de secretos
├── .streamlit/secrets.toml.example
└── tests/
```

---

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate          # Windows

pip install -r requirements.txt
```

## Configuración de secretos (opcional)

Copiá `.env.example` a `.env` (o configurá los secretos en Streamlit Cloud) con
las API keys que quieras usar. **Ninguna es obligatoria**; sin claves, la app
funciona con los proveedores gratuitos.

| Proveedor | Variable | Necesaria para |
|-----------|----------|----------------|
| Groq | `GROQ_API_KEY` | STT con Whisper + evaluación con LLM |
| AssemblyAI | `ASSEMBLYAI_API_KEY` | STT alternativo |
| ElevenLabs | `ELEVENLABS_API_KEY` | TTS de alta calidad |
| OpenAI | `OPENAI_API_KEY` | TTS alternativo |
| D-ID | `DID_API_KEY` | Avatar animado |
| Firebase | `FIREBASE_SERVICE_ACCOUNT` (o `_PATH`) | Banco de preguntas desde Firestore |

## Ejecución

```bash
streamlit run app.py
```

## Validar el banco de preguntas

```bash
python scripts/check_questions.py
```

---

## Cómo funciona

1. El estudiante elige (o no) una categoría y presiona **"Escuchar pregunta"**
   para oírla por voz.
2. Graba su respuesta con el micrófono.
3. La app la **transcribe** (STT).
4. La **evalúa**:
   - **LLM** (si hay `GROQ_API_KEY`): compara con el contexto ideal y devuelve
     una calificación 0–100 con feedback motivador.
   - **Palabras clave** (fallback gratuito): mide cuántas palabras clave
     esperadas aparecen en la respuesta.
5. Genera el **feedback por voz** (TTS) y, si hay `DID_API_KEY`, un **avatar**.
6. Guarda el resultado en el **historial** y permite **exportar CSV/PDF**.

---

## Banco de preguntas

Cada pregunta en `data/preguntas.json` tiene:

```json
{
  "id": "func-01",
  "categoria": "Funciones",
  "dificultad": "basico",
  "pregunta": "¿Con qué palabra clave se define una función en Python?",
  "palabras_clave": ["def", "función", "parámetros"],
  "contexto_ideal": "Con la palabra clave `def`..."
}
```

- `palabras_clave` se usa en el modo gratuito (coincidencia).
- `contexto_ideal` es la referencia que usa el LLM para la rúbrica.

Agregá más preguntas editando el JSON. `scripts/check_questions.py` valida su
estructura.

### Banco de preguntas desde Firebase (opcional)

Podés servir las preguntas desde **Firestore** (colección `cursos`), en lugar
del JSON local. Estructura esperada:

```
cursos/<curso_id> -> {
  "titulo": "Curso de Python",
  "capitulos": {
    "cap_01": {
      "titulo": "Fundamentos",
      "evaluacion": {
        "instructor_pregunta": "¿...?",
        "contexto_respuesta": "respuesta ideal...",
        "palabras_clave": ["print", "consola"]   // opcional
      }
    }
  }
}
```

Para activarlo:

1. Configurá `FIREBASE_SERVICE_ACCOUNT` (JSON de la cuenta de servicio) o
   `FIREBASE_SERVICE_ACCOUNT_PATH` (ruta a un archivo no versionado).
2. En `config.py`, seteá `question_source = "firebase"` (o dejá `"auto"`) y
   `firebase_course_id` con el id del documento.

La app detecta la fuente automáticamente y cae al JSON local si Firebase no
está configurado o falla.

---

## Guía de estudio

Los errores de los repositorios originales y sus correcciones están explicados
en **[GUIA_DE_ESTUDIO.md](GUIA_DE_ESTUDIO.md)**.

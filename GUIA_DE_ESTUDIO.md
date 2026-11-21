# Guía de estudio — errores de los tres repositorios y sus correcciones

Al integrar `evaluador_audio`, `Evaluador_interactivo` y `Evaluador-Stl-avatar`
en un solo proyecto, encontramos los siguientes problemas. Cada uno sigue el
formato **problema → por qué es un error → corrección**.

---

## 1. Secretos hardcodeados en el código

### El problema
`evaluador_audio/evaluacion.py` tenía la ruta a una clave de servicio de Firebase
hardcodeada:

```python
SERVICE_ACCOUNT_KEY_PATH = 'bootcampxperience-ia-3a73df743c74.json'
```

Y la pregunta actual también estaba hardcodeada en `app.py`.

### Por qué es un error
Las claves y credenciales **nunca** deben ir en el código: si el repo se hace
público (o lo clona alguien), la credencial queda expuesta. Además, hace el
proyecto no portable.

### La corrección
- Los secretos se leen de `st.secrets` o variables de entorno (`.env`), con
  `config.get_secret()`.
- Se agregó `.env.example` y `.streamlit/secrets.toml.example` como plantillas.
- El `.gitignore` ahora ignora `.env`, `.streamlit/secrets.toml` y cualquier
  `*-service-account*.json`.

---

## 2. Código muerto y basura versionada

### El problema
`evaluador_audio` tenía commiteados:

- `__pycache__/` (bytecode compilado).
- `Old/` (versiones viejas de scripts).
- `media/` (mp3s de prueba: `response.mp3`, `feedback_profesor.mp3`).

### Por qué es un error
El bytecode y los binarios no pertenecen a git (ensucian el repo y cambian con
cada ejecución). Las carpetas `Old/` duplican lógica que ya no se usa.

### La corrección
`.gitignore` ahora ignora `__pycache__/`, `*.pyc`, `Old/`, `media/` y `*.mp3`.

---

## 3. `gitignore` sin punto

### El problema
`Evaluador_interactivo` tenía un archivo llamado `gitignore` (sin el punto),
por lo que git lo ignoraba... es decir, **no lo aplicaba**.

### Por qué es un error
Un `.gitignore` mal nombrado no tiene efecto: git no lo reconoce.

### La corrección
Se creó un `.gitignore` correcto (con punto) en el proyecto integrado.

---

## 4. Tres lógicas de puntaje distintas

### El problema
Cada repo evaluaba distinto:
- `Evaluador_interactivo`: coincidencia de palabras clave.
- `evaluador_audio`: evaluación semántica con LLM (rúbrica 0–100).
- `Evaluador-Stl-avatar`: puntaje **manual** con un slider.

### Por qué es un error
Tener tres formas incompatibles de puntuar hace imposible comparar resultados
entre sí.

### La corrección
Se unificó en **dos modos explícitos**:
- `llm` (semántico, rúbrica 0–100) cuando hay `GROQ_API_KEY`.
- `keywords` (coincidencia, gratuito) como fallback.

El `evaluator.py` centraliza ambos, y la app elige automáticamente según las
claves disponibles.

---

## 5. Funciones duplicadas entre repos

### El problema
`generar_video_did()` y `generar_mensaje()` estaban **copiadas** en
`Evaluador_interactivo` y `Evaluador-Stl-avatar`, con pequeñas diferencias.

### Por qué es un error
Dos copias de la misma lógica divergen con el tiempo y nadie sabe cuál es la
correcta.

### La corrección
Una sola implementación en `src/avatar.py` (`generar_video`) y
`src/evaluator.py` (`generar_mensaje`), reutilizada por la app.

---

## 6. Salida del LLM sin estructura

### El problema
`evaluador_audio/request_model.py` devolvía el feedback como **texto libre**,
mientras que `evaluacion.py` (otra versión) usaba LangChain + Pydantic para
garantizar un JSON estructurado con la calificación.

### Por qué es un error
Con texto libre es difícil extraer la nota numérica de forma confiable para
guardarla o graficarla.

### La corrección
`src/llm.py` pide al modelo un **JSON estructurado** (`feedback` + `calificacion`)
y lo parsea con tolerancia (regex como último recurso). Así la nota siempre es
un número 0–100 usable.

---

## 7. Modelo inconsistente en el código

### El problema
En `request_model.py` el comentario decía `llama-3.1-8b-instant` pero el código
usaba `"llama3-8b-8192"`.

### Por qué es un error
La documentación que no matchea el código confunde y puede llevar a creer que se
usa un modelo distinto.

### La corrección
El nombre del modelo es una constante en `config.py` (`llm_model`), documentada
y consistente.

---

## 8. `requirements.txt` inconsistentes

### El problema
- `evaluador_audio`: un `pip freeze` de 80+ paquetes (con dependencias de
  Jupyter, `asarPy`, etc. que no se usan).
- `Evaluador_interactivo`: 6 paquetes sin versionar (`streamlit>=1.25`, etc.).

### Por qué es un error
Un `pip freeze` trae dependencias transitorias y conflictos; sin versionar no es
reproducible.

### La corrección
`requirements.txt` con **solo las dependencias reales, pineadas**: streamlit,
SpeechRecognition, groq, assemblyai, gTTS, openai, pydantic, langchain-core,
langchain-groq, requests, pandas, fpdf, python-dotenv.

---

## 9. Sin manejo de proveedores ni fallback

### El problema
Cada repo dependía de un proveedor específico (Groq **o** Google **o** D-ID), sin
una forma de elegir ni de caer a una opción gratuita.

### Por qué es un error
Si no tenías la API key de Groq, la app de `evaluador_audio` no funcionaba, sin
alternativa.

### La corrección
`config.Config.resolve()` elige el proveedor **automáticamente** según las API
keys disponibles, cayendo a las variantes gratuitas (Google STT, gTTS, keywords).

---

## Resumen rápido

| # | Error | Corrección |
|---|-------|------------|
| 1 | Secretos hardcodeados | `get_secret()` + `.env.example` |
| 2 | `__pycache__`/`Old`/`media` en git | `.gitignore` correcto |
| 3 | `gitignore` sin punto | `.gitignore` |
| 4 | 3 lógicas de puntaje | 2 modos unificados (`llm`/`keywords`) |
| 5 | Funciones duplicadas | un solo `avatar.py`/`evaluator.py` |
| 6 | Salida LLM sin estructura | JSON estructurado + parseo tolerante |
| 7 | Modelo inconsistente | constante en `config.py` |
| 8 | `requirements.txt` malos | deps reales y pineadas |
| 9 | Sin fallback de proveedor | `Config.resolve()` con fallback gratis |

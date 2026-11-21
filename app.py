"""Evaluador oral de Python — interfaz Streamlit unificada.

Consolida los tres repositorios originales (evaluador_audio, Evaluador_interactivo
y Evaluador-Stl-avatar) en una sola app con:

- Banco de preguntas por categoría y dificultad.
- Reconocimiento de voz (Groq/AssemblyAI/Google) y síntesis (ElevenLabs/OpenAI/gTTS).
- Evaluación semántica con LLM (rúbrica 0–100) o por palabras clave (gratuita).
- Feedback por voz y avatar opcional (D-ID).
- Historial de resultados + exportación CSV/PDF.

Ejecutar:  streamlit run app.py
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from config import Config, get_secret
from src import avatar, evaluator, export, firebase_store, llm, questions as qbank, store, stt, tts

# ------------------------------------------------------------------ Configuración
st.set_page_config(page_title="Evaluador Oral de Python", layout="wide")

cfg = Config()
resolved = cfg.resolve()

# ------------------------------------------------------------------ Sidebar
st.sidebar.title("⚙️ Configuración")
nombre = st.sidebar.text_input("Nombre del estudiante", value="Estudiante")

# Proveedores efectivos (auto-resueltos según API keys disponibles).
st.sidebar.markdown("**Proveedores activos**")
st.sidebar.caption(
    f"🎤 Voz→texto: `{resolved['stt']}` · 🔉 Texto→voz: `{resolved['tts']}` · "
    f"🧠 Evaluación: `{resolved['eval_mode']}` · 🧑‍🏫 Avatar: "
    f"{'sí' if resolved['avatar_disponible'] else 'no'}"
)

did_key = get_secret("DID_API_KEY")

# ------------------------------------------------------------------ Banco de preguntas
def _cargar_preguntas(cfg, resolved):
    """Carga preguntas desde Firebase (si está configurado) o del JSON local."""
    if resolved["question_source"] == "firebase":
        try:
            sa = cfg.get_firebase_service_account()
            db = firebase_store.init_firestore(sa)
            preguntas = firebase_store.load_questions_from_firestore(
                db, cfg.firebase_course_id
            )
            if preguntas:
                return preguntas, "firebase"
            st.sidebar.warning(
                "Firebase configurado pero sin preguntas para el curso. "
                "Usando el banco local (JSON)."
            )
        except Exception as exc:  # noqa: BLE001
            st.sidebar.warning(f"No se pudo conectar a Firebase ({exc}). Usando JSON local.")
    return qbank.load_questions(cfg.questions_path), "json"


preguntas, fuente_preguntas = _cargar_preguntas(cfg, resolved)
st.sidebar.caption(f"📚 Banco de preguntas: `{fuente_preguntas}`")
categorias = ["Todas"] + qbank.categories(preguntas)
categoria_elegida = st.sidebar.selectbox("Categoría", categorias)
preguntas_filtradas = qbank.filter_by_category(
    preguntas, None if categoria_elegida == "Todas" else categoria_elegida
)

# ------------------------------------------------------------------ Estado de sesión
if "pregunta_idx" not in st.session_state:
    st.session_state.pregunta_idx = 0
if "resultados" not in st.session_state:
    st.session_state.resultados = store.load_results(cfg.results_path)
if "respuesta_transcrita" not in st.session_state:
    st.session_state.respuesta_transcrita = None
if "evaluacion" not in st.session_state:
    st.session_state.evaluacion = None

# ------------------------------------------------------------------ Pregunta actual
if not preguntas_filtradas:
    st.warning("No hay preguntas disponibles para esta categoría.")
    st.stop()

idx = min(st.session_state.pregunta_idx, len(preguntas_filtradas) - 1)
pregunta_actual = preguntas_filtradas[idx]

st.markdown("## 🎓 Evaluador Oral de Python")
st.markdown(f"### Pregunta {idx + 1} de {len(preguntas_filtradas)} — {pregunta_actual.get('categoria', '')}")
st.info(f"**{pregunta_actual['pregunta']}**")

# ------------------------------------------------------------------ Dos columnas
col_est, col_prof = st.columns(2)

# ---- Estudiante (izquierda)
with col_est:
    st.markdown("### 🎤 Tu respuesta")

    if st.button("🔊 Escuchar pregunta", key="escuchar"):
        audio_pregunta = tts.text_to_speech(
            pregunta_actual["pregunta"], resolved["tts"],
            get_secret("ELEVENLABS_API_KEY"), get_secret("OPENAI_API_KEY"),
        )
        if audio_pregunta:
            st.audio(audio_pregunta, format="audio/mp3")

    audio_bytes = st.audio_input("Grabá tu respuesta", key=f"audio_{idx}")
    if audio_bytes:
        with st.spinner("Transcribiendo..."):
            texto = stt.transcribe(
                audio_bytes.read(), resolved["stt"],
                get_secret("GROQ_API_KEY") or get_secret("ASSEMBLYAI_API_KEY"),
                model=cfg.stt_model,
            )
        if texto:
            st.session_state.respuesta_transcrita = texto
            st.session_state.evaluacion = None
        else:
            st.error("No se pudo transcribir el audio. Intentá de nuevo.")

    if st.session_state.respuesta_transcrita:
        st.markdown("**Transcripción:**")
        st.success(st.session_state.respuesta_transcrita)

# ---- Instructor (derecha)
with col_prof:
    st.markdown("### 🧑‍🏫 Evaluación")
    if st.session_state.evaluacion:
        ev = st.session_state.evaluacion
        nota = ev["calificacion"]
        emoji, color = evaluator.grade_band(nota)
        st.markdown(
            f"#### Calificación: <span style='color:{color}; font-size:1.4em'>**{nota}/100** {emoji}</span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"> {ev['feedback']}")

        if st.session_state.get("feedback_audio"):
            st.audio(st.session_state["feedback_audio"], format="audio/mp3")
    else:
        st.write("Esperando tu respuesta para evaluar...")

# ------------------------------------------------------------------ Botones
st.markdown("---")
c1, c2, c3 = st.columns([2, 1, 2])

with c2:
    if st.button("🧠 Evaluar respuesta", use_container_width=True):
        if not st.session_state.respuesta_transcrita:
            st.warning("Grabá tu respuesta primero.")
        else:
            with st.spinner("Evaluando..."):
                if resolved["eval_mode"] == "llm":
                    ev = llm.evaluar_con_llm(
                        pregunta_actual["pregunta"],
                        pregunta_actual["contexto_ideal"],
                        st.session_state.respuesta_transcrita,
                        get_secret("GROQ_API_KEY"),
                        model=cfg.llm_model,
                    )
                else:
                    aciertos, total = evaluator.score_keywords(
                        st.session_state.respuesta_transcrita, pregunta_actual["palabras_clave"]
                    )
                    ev = {
                        "feedback": (
                            f"Cubriste {aciertos} de {total} palabras clave esperadas. "
                            f"{evaluator.generar_mensaje(nombre, aciertos, total)}"
                        ),
                        "calificacion": evaluator.coverage_to_grade(aciertos, total),
                    }

            if ev:
                st.session_state.evaluacion = ev

                # Feedback por voz (TTS).
                with st.spinner("Generando voz del feedback..."):
                    st.session_state.feedback_audio = tts.text_to_speech(
                        ev["feedback"], resolved["tts"],
                        get_secret("ELEVENLABS_API_KEY"), get_secret("OPENAI_API_KEY"),
                    )

                # Guardar resultado.
                resultado = {
                    "fecha": datetime.now().isoformat(timespec="seconds"),
                    "estudiante": nombre,
                    "categoria": pregunta_actual.get("categoria", ""),
                    "pregunta": pregunta_actual["pregunta"],
                    "respuesta": st.session_state.respuesta_transcrita,
                    "puntaje": ev["calificacion"],
                    "modo": resolved["eval_mode"],
                }
                st.session_state.resultados = store.save_result(cfg.results_path, resultado)
                st.rerun()
            else:
                st.error("No se pudo evaluar. Revisá las API keys o intentá de nuevo.")

# ------------------------------------------------------------------ Avatar (opcional)
if st.session_state.evaluacion and resolved["avatar_disponible"]:
    with st.expander("🧑‍🏫 Avatar del instructor", expanded=False):
        mensaje = evaluator.generar_mensaje(
            nombre, st.session_state.evaluacion["calificacion"], 100
        )
        with st.spinner("Generando avatar..."):
            video_url = avatar.generar_video(did_key, st.session_state.evaluacion["feedback"])
        if video_url:
            st.video(video_url)
        else:
            st.warning("No se pudo generar el video del avatar.")

# ------------------------------------------------------------------ Próxima pregunta
col_n1, col_n2, col_n3 = st.columns([2, 1, 2])
with col_n2:
    if idx < len(preguntas_filtradas) - 1:
        if st.button("Próxima pregunta →", use_container_width=True):
            st.session_state.pregunta_idx += 1
            st.session_state.respuesta_transcrita = None
            st.session_state.evaluacion = None
            st.session_state.feedback_audio = None
            st.rerun()
    else:
        st.success("🎉 ¡Completaste todas las preguntas de esta categoría!")

# ------------------------------------------------------------------ Historial + export
st.markdown("---")
with st.expander("📊 Historial y resultados", expanded=False):
    if st.session_state.resultados:
        df = export.to_dataframe(st.session_state.resultados)
        st.dataframe(df)

        # Dashboard simple: promedio por categoría.
        if "categoria" in df.columns and "puntaje" in df.columns:
            st.markdown("**Promedio por categoría**")
            st.bar_chart(df.groupby("categoria")["puntaje"].mean())

        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            st.download_button(
                "📥 Descargar CSV", export.to_csv(st.session_state.resultados),
                "resultados.csv", "text/csv",
            )
        with col_exp2:
            st.download_button(
                "📥 Descargar PDF", export.to_pdf(st.session_state.resultados),
                "resultados.pdf", "application/pdf",
            )
    else:
        st.info("Aún no hay resultados guardados.")

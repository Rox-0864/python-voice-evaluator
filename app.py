"""Evaluador oral de Python — interfaz Streamlit unificada.

Consolida los tres repositorios originales (evaluador_audio, Evaluador_interactivo
y Evaluador-Stl-avatar) en una sola app con:

- Banco de preguntas por categoría y dificultad (JSON local o Firestore).
- Reconocimiento de voz (Groq/AssemblyAI/Google) y síntesis (ElevenLabs/OpenAI/gTTS).
- Evaluación semántica con LLM (rúbrica 0–100) o por palabras clave (gratuita).
- Dos modos: Práctica (feedback inmediato) y Examen (con temporizador).
- Feedback por voz y avatar opcional (D-ID).
- Historial de resultados + exportación CSV/PDF.

Ejecutar:  streamlit run app.py
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

# Garantiza que la raíz del repo esté en sys.path (necesario en Streamlit Cloud).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

from config import Config, get_secret  # noqa: E402
from src import avatar, evaluator, export, firebase_store, llm  # noqa: E402
from src import questions as qbank  # noqa: E402
from src import store, stt, tts  # noqa: E402
from src.exam import select_questions, summarize_exam  # noqa: E402


# ================================================================== Helpers
def _evaluar(pregunta: dict, respuesta: str, resolved: dict) -> dict:
    """Evalúa una respuesta y devuelve {'feedback': str, 'calificacion': int}."""
    if resolved["eval_mode"] == "llm":
        return llm.evaluar_con_llm(
            pregunta["pregunta"],
            pregunta["contexto_ideal"],
            respuesta,
            get_secret("GROQ_API_KEY"),
            model=cfg.llm_model,
        )
    aciertos, total = evaluator.score_keywords(respuesta, pregunta["palabras_clave"])
    return {
        "feedback": f"Cubriste {aciertos} de {total} palabras clave esperadas.",
        "calificacion": evaluator.coverage_to_grade(aciertos, total),
    }


def _cargar_preguntas(cfg, resolved):
    """Carga preguntas desde Firebase (si está configurado) o del JSON local."""
    if resolved["question_source"] == "firebase":
        try:
            sa = cfg.get_firebase_service_account()
            db = firebase_store.init_firestore(sa)
            preguntas = firebase_store.load_questions_from_firestore(db, cfg.firebase_course_id)
            if preguntas:
                return preguntas, "firebase"
            st.sidebar.warning("Firebase sin preguntas para el curso. Usando JSON local.")
        except Exception as exc:  # noqa: BLE001
            st.sidebar.warning(f"No se pudo conectar a Firebase ({exc}). Usando JSON local.")
    return qbank.load_questions(cfg.questions_path), "json"


def _render_practica(preguntas, categorias, nombre, resolved, did_key):
    categoria_elegida = st.sidebar.selectbox("Categoría", categorias)
    filtradas = qbank.filter_by_category(
        preguntas, None if categoria_elegida == "Todas" else categoria_elegida
    )

    if "pregunta_idx" not in st.session_state:
        st.session_state.pregunta_idx = 0
    if "resultados" not in st.session_state:
        st.session_state.resultados = store.load_results(cfg.results_path)
    if "respuesta_transcrita" not in st.session_state:
        st.session_state.respuesta_transcrita = None
    if "evaluacion" not in st.session_state:
        st.session_state.evaluacion = None

    if not filtradas:
        st.warning("No hay preguntas disponibles para esta categoría.")
        st.stop()

    idx = min(st.session_state.pregunta_idx, len(filtradas) - 1)
    pregunta_actual = filtradas[idx]

    st.markdown("## 🎓 Evaluador Oral de Python")
    st.markdown(f"### Pregunta {idx + 1} de {len(filtradas)} — {pregunta_actual.get('categoria', '')}")
    st.info(f"**{pregunta_actual['pregunta']}**")

    col_est, col_prof = st.columns(2)

    with col_est:
        st.markdown("### 🎤 Tu respuesta")
        if st.button("🔊 Escuchar pregunta", key="escuchar"):
            audio_p = tts.text_to_speech(
                pregunta_actual["pregunta"], resolved["tts"],
                get_secret("ELEVENLABS_API_KEY"), get_secret("OPENAI_API_KEY"),
            )
            if audio_p:
                st.audio(audio_p, format="audio/mp3")

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
                st.error("No se pudo transcribir el audio.")

        if st.session_state.respuesta_transcrita:
            st.markdown("**Transcripción:**")
            st.success(st.session_state.respuesta_transcrita)

    with col_prof:
        st.markdown("### 🧑‍🏫 Evaluación")
        if st.session_state.evaluacion:
            ev = st.session_state.evaluacion
            emoji, color = evaluator.grade_band(ev["calificacion"])
            st.markdown(
                f"#### Calificación: <span style='color:{color}; font-size:1.4em'>**{ev['calificacion']}/100** {emoji}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(f"> {ev['feedback']}")
            if st.session_state.get("feedback_audio"):
                st.audio(st.session_state["feedback_audio"], format="audio/mp3")
        else:
            st.write("Esperando tu respuesta para evaluar...")

    st.markdown("---")
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        if st.button("🧠 Evaluar respuesta", use_container_width=True):
            if not st.session_state.respuesta_transcrita:
                st.warning("Grabá tu respuesta primero.")
            else:
                with st.spinner("Evaluando..."):
                    ev = _evaluar(pregunta_actual, st.session_state.respuesta_transcrita, resolved)
                if ev:
                    st.session_state.evaluacion = ev
                    with st.spinner("Generando voz del feedback..."):
                        st.session_state.feedback_audio = tts.text_to_speech(
                            ev["feedback"], resolved["tts"],
                            get_secret("ELEVENLABS_API_KEY"), get_secret("OPENAI_API_KEY"),
                        )
                    resultado = {
                        "fecha": datetime.now().isoformat(timespec="seconds"),
                        "estudiante": nombre,
                        "categoria": pregunta_actual.get("categoria", ""),
                        "pregunta": pregunta_actual["pregunta"],
                        "respuesta": st.session_state.respuesta_transcrita,
                        "puntaje": ev["calificacion"],
                        "modo": "practica",
                    }
                    st.session_state.resultados = store.save_result(cfg.results_path, resultado)
                    st.rerun()
                else:
                    st.error("No se pudo evaluar. Revisá las API keys.")

    if st.session_state.evaluacion and resolved["avatar_disponible"]:
        with st.expander("🧑‍🏫 Avatar del instructor", expanded=False):
            with st.spinner("Generando avatar..."):
                video_url = avatar.generar_video(did_key, st.session_state.evaluacion["feedback"])
            if video_url:
                st.video(video_url)
            else:
                st.warning("No se pudo generar el video del avatar.")

    col_n1, col_n2, col_n3 = st.columns([2, 1, 2])
    with col_n2:
        if idx < len(filtradas) - 1:
            if st.button("Próxima pregunta →", use_container_width=True):
                st.session_state.pregunta_idx += 1
                st.session_state.respuesta_transcrita = None
                st.session_state.evaluacion = None
                st.session_state.feedback_audio = None
                st.rerun()
        else:
            st.success("🎉 ¡Completaste todas las preguntas de esta categoría!")

    _render_historial(st.session_state.resultados)


def _render_examen(preguntas, categorias, nombre, resolved, did_key):
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Examen**")
    cat_examen = st.sidebar.selectbox("Categoría del examen", categorias)
    n_preguntas = st.sidebar.slider("Número de preguntas", 1, 10, 5)
    minutos = st.sidebar.slider("Tiempo límite (minutos)", 1, 30, 5)

    if "examen_activo" not in st.session_state:
        st.session_state.examen_activo = False

    if st.sidebar.button("🚀 Iniciar examen", use_container_width=True):
        pool = qbank.filter_by_category(
            preguntas, None if cat_examen == "Todas" else cat_examen
        )
        st.session_state.examen_preguntas = select_questions(pool, n_preguntas)
        st.session_state.examen_idx = 0
        st.session_state.examen_inicio = time.time()
        st.session_state.examen_limite = minutos * 60
        st.session_state.examen_respuestas = []
        st.session_state.examen_respuesta = None
        st.session_state.examen_activo = True
        st.rerun()

    if not st.session_state.examen_activo:
        st.markdown("## 📝 Modo Examen")
        st.info(
            "Configurá el examen en la barra lateral (categoría, número de preguntas "
            "y tiempo límite) y presioná **Iniciar examen**. El feedback se mostrará "
            "recién al final."
        )
        return

    preguntas_examen = st.session_state.examen_preguntas
    idx = st.session_state.examen_idx
    limite = st.session_state.examen_limite
    transcurrido = time.time() - st.session_state.examen_inicio
    restante = int(max(0, limite - transcurrido))

    if restante == 0 or idx >= len(preguntas_examen):
        _render_examen_final(nombre)
        return

    mm, ss = divmod(restante, 60)
    st.sidebar.markdown(f"### ⏱️ Tiempo restante: `{mm:02d}:{ss:02d}`")
    st.sidebar.caption("El cronómetro se actualiza con cada interacción.")

    pregunta_actual = preguntas_examen[idx]
    st.markdown("## 📝 Examen de Python")
    st.markdown(f"### Pregunta {idx + 1} de {len(preguntas_examen)}")
    st.info(f"**{pregunta_actual['pregunta']}**")

    audio_bytes = st.audio_input("Grabá tu respuesta", key=f"examen_audio_{idx}")
    if audio_bytes:
        with st.spinner("Transcribiendo..."):
            texto = stt.transcribe(
                audio_bytes.read(), resolved["stt"],
                get_secret("GROQ_API_KEY") or get_secret("ASSEMBLYAI_API_KEY"),
                model=cfg.stt_model,
            )
        if texto:
            st.session_state.examen_respuesta = texto
        else:
            st.error("No se pudo transcribir el audio.")

    if st.session_state.examen_respuesta:
        st.markdown("**Transcripción:**")
        st.success(st.session_state.examen_respuesta)

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("✔️ Responder y siguiente", use_container_width=True):
            if not st.session_state.examen_respuesta:
                st.warning("Grabá tu respuesta primero.")
            else:
                with st.spinner("Evaluando..."):
                    ev = _evaluar(pregunta_actual, st.session_state.examen_respuesta, resolved)
                st.session_state.examen_respuestas.append(
                    {
                        "pregunta": pregunta_actual["pregunta"],
                        "categoria": pregunta_actual.get("categoria", ""),
                        "respuesta": st.session_state.examen_respuesta,
                        "puntaje": ev["calificacion"] if ev else 0,
                    }
                )
                st.session_state.examen_idx += 1
                st.session_state.examen_respuesta = None
                st.rerun()

        if st.button("🏁 Finalizar examen", use_container_width=True):
            st.session_state.examen_idx = len(preguntas_examen)
            st.rerun()


def _render_examen_final(nombre):
    respuestas = st.session_state.examen_respuestas
    resumen = summarize_exam(respuestas)

    st.markdown("## 🏁 Resultados del examen")
    st.markdown(f"**Estudiante:** {nombre} · **Preguntas:** {resumen['n']}")

    if resumen["aprobado"]:
        st.success(f"### ✅ Aprobado — Promedio: {resumen['promedio']}/100")
    else:
        st.error(f"### ❌ Reprobado — Promedio: {resumen['promedio']}/100")

    if respuestas:
        st.dataframe(export.to_dataframe(respuestas))
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Descargar CSV", export.to_csv(respuestas), "examen.csv", "text/csv"
            )
        with col2:
            st.download_button(
                "📥 Descargar PDF", export.to_pdf(respuestas), "examen.pdf", "application/pdf"
            )

    if st.button("🔄 Nuevo examen", use_container_width=True):
        st.session_state.examen_activo = False
        st.rerun()


def _render_historial(resultados):
    st.markdown("---")
    with st.expander("📊 Historial y resultados", expanded=False):
        if resultados:
            df = export.to_dataframe(resultados)
            st.dataframe(df)
            if "categoria" in df.columns and "puntaje" in df.columns:
                st.markdown("**Promedio por categoría**")
                st.bar_chart(df.groupby("categoria")["puntaje"].mean())
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📥 Descargar CSV", export.to_csv(resultados), "resultados.csv", "text/csv"
                )
            with col2:
                st.download_button(
                    "📥 Descargar PDF", export.to_pdf(resultados), "resultados.pdf", "application/pdf"
                )
        else:
            st.info("Aún no hay resultados guardados.")


# ================================================================== App principal
st.set_page_config(page_title="Evaluador Oral de Python", layout="wide")

cfg = Config()
resolved = cfg.resolve()

st.sidebar.title("⚙️ Configuración")
nombre = st.sidebar.text_input("Nombre del estudiante", value="Estudiante")

st.sidebar.markdown("**Proveedores activos**")
st.sidebar.caption(
    f"🎤 `{resolved['stt']}` · 🔉 `{resolved['tts']}` · 🧠 `{resolved['eval_mode']}` · "
    f"🧑‍🏫 {'sí' if resolved['avatar_disponible'] else 'no'}"
)
did_key = get_secret("DID_API_KEY")

preguntas, fuente_preguntas = _cargar_preguntas(cfg, resolved)
st.sidebar.caption(f"📚 Banco de preguntas: `{fuente_preguntas}`")

categorias = ["Todas"] + qbank.categories(preguntas)
modo = st.sidebar.radio("Modo", ["Práctica", "Examen"])

if modo == "Examen":
    _render_examen(preguntas, categorias, nombre, resolved, did_key)
else:
    _render_practica(preguntas, categorias, nombre, resolved, did_key)

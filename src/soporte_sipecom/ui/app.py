"""Consola SIPECOM-SOPORTE. Chat nativo Streamlit (chat_input + sidebar)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time

import streamlit as st
import yaml

from soporte_sipecom.config import DEFAULT_PORT, load as load_cfg
from soporte_sipecom.detect import which
from soporte_sipecom.engine import run_engine

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
DEFAULT_CATALOGO = Path(
    r"C:/Users/kfernandez/projects/seguridad/prueba del desposte/salida/chef/catalogo.yaml"
)
UPLOADS = HERE / ".uploads"
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
GROK_MODELS = ["grok-4.6", "grok-4.5"]
CODEX_MODELS = ["gpt-6-astra"]
EFFORTS = ["low", "medium", "high", "xhigh"]
API_PROVIDERS = ["OpenAI", "xAI (Grok)", "Anthropic (Claude)"]
SIPI = ASSETS / "sipi-colibri.png"
LOGO = ASSETS / "sipecom-logo.png"


def load_catalog() -> dict:
    env = Path(__import__("os").environ.get("SOPORTE_CATALOGO") or "")
    for candidate in (env, HERE / "catalogo.yaml", DEFAULT_CATALOGO):
        if candidate and Path(candidate).is_file():
            data = yaml.safe_load(Path(candidate).read_text(encoding="utf-8")) or {}
            data.setdefault("motor_default", "grok")
            data.setdefault("timeout_s", 240)
            data.setdefault("proyectos", [])
            return data
    return {"motor_default": "grok", "timeout_s": 240, "proyectos": []}


def save_uploads(files) -> list[Path]:
    if not files:
        return []
    UPLOADS.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS / str(int(time.time() * 1000))
    dest.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for uploaded in files:
        name = Path(getattr(uploaded, "name", "archivo")).name or "archivo"
        path = dest / name
        path.write_bytes(uploaded.getvalue())
        paths.append(path)
    return paths


st.set_page_config(
    page_title="Consola de Soporte · Sipecom",
    page_icon=str(SIPI) if SIPI.is_file() else ":material/support_agent:",
    layout="wide",
    initial_sidebar_state="expanded",
)

if LOGO.is_file():
    st.logo(str(LOGO), size="large")

catalog = load_catalog()
proyectos = catalog.get("proyectos") or []
cfg = load_cfg()
saved_agents = cfg.get("agents") or ["grok", "codex"]

if "messages" not in st.session_state:
    st.session_state.messages = []

if not proyectos:
    st.warning("No hay catalogo.yaml.")
    st.stop()

names = [p.get("nombre") or p.get("id") for p in proyectos]

with st.sidebar:
    st.subheader("Proyecto")
    choice = st.selectbox("Origen", names)
    proyecto = proyectos[names.index(choice)]

    st.subheader("Modo de ejecución")
    modo = st.segmented_control(
        "Modo",
        options=["CLI local", "API key"],
        default="CLI local",
        label_visibility="collapsed",
    )

    st.subheader("Motor")
    if modo == "CLI local":
        clis = [a for a in ("grok", "codex") if a in saved_agents] or ["grok", "codex"]
        motor = st.selectbox("CLI", clis)
        modelos = GROK_MODELS if motor == "grok" else CODEX_MODELS
        st.caption("Sesión de esta PC. Sin API keys.")
        st.caption(f"codex `{which('codex') or '—'}`")
        st.caption(f"grok `{which('grok') or '—'}`")
    else:
        motor = "grok"
        st.selectbox("Proveedor", API_PROVIDERS)
        st.text_input("API key", type="password", placeholder="sk-…")
        modelos = GROK_MODELS + CODEX_MODELS
        st.caption("La key no se guarda en disco.")

    modelo = st.selectbox("Modelo", modelos)
    extra = st.text_input("Modelo extra (opcional)", placeholder="id de modelo")
    if extra.strip():
        modelo = extra.strip()
    effort = st.selectbox("Effort", EFFORTS, index=EFFORTS.index("medium"))

    st.divider()
    if SIPI.is_file():
        st.image(str(SIPI), width=44)
    st.markdown("**Sipi**")
    st.caption("Asistente de soporte · Sipecom")
    st.caption(f"© {datetime.now().year} · puerto {DEFAULT_PORT}")

# --- only chat ---
for item in st.session_state.messages:
    avatar = str(SIPI) if item["role"] == "assistant" and SIPI.is_file() else None
    kwargs = {"avatar": avatar} if avatar else {}
    with st.chat_message(item["role"], **kwargs):
        if item.get("command"):
            st.code(item["command"], language="bash")
        if item.get("content"):
            st.markdown(item["content"])
        for path in item.get("adjuntos") or []:
            p = Path(path)
            if p.suffix.lower() in IMAGE_EXT and p.is_file():
                st.image(str(p), caption=p.name)
        if item.get("motor"):
            st.caption(f"motor: `{item['motor']}`")

prompt = st.chat_input(
    "Escribe un mensaje",
    accept_file="multiple",
    file_type=["jpg", "jpeg", "png", "webp", "gif"],
    submit_mode="disable",
)

if prompt:
    text = (prompt.text or "") if hasattr(prompt, "text") else str(prompt)
    files = list(getattr(prompt, "files", None) or [])
    adjuntos = save_uploads(files)

    st.session_state.messages.append(
        {"role": "user", "content": text, "adjuntos": [str(p) for p in adjuntos]}
    )
    with st.chat_message("user"):
        if text:
            st.markdown(text)
        for p in adjuntos:
            if p.suffix.lower() in IMAGE_EXT:
                st.image(str(p), caption=p.name)

    with st.chat_message("assistant", avatar=str(SIPI) if SIPI.is_file() else None):
        with st.status(":shimmer[Escribiendo]", type="compact") as status:
            if modo != "CLI local":
                answer, used, cmd = (
                    "Modo API key: aún no ejecuta remoto. Cambia a CLI local.",
                    "none",
                    "",
                )
            else:
                answer, used, cmd = run_engine(
                    motor,
                    modelo,
                    effort,
                    proyecto,
                    text,
                    adjuntos,
                    int(catalog.get("timeout_s") or 240),
                )
            status.update(label="Listo", state="complete")
        if cmd:
            st.code(cmd, language="bash")
        st.markdown(answer)
        if used:
            st.caption(f"motor: `{used}`")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "motor": used, "command": cmd}
    )

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
from soporte_sipecom.ingest import add_project, load_catalog, save_catalog

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


def seed_catalog() -> dict:
    data = load_catalog()
    if data.get("proyectos"):
        return data
    if DEFAULT_CATALOGO.is_file():
        seeded = yaml.safe_load(DEFAULT_CATALOGO.read_text(encoding="utf-8")) or {}
        seeded.setdefault("motor_default", "grok")
        seeded.setdefault("timeout_s", 240)
        seeded.setdefault("proyectos", [])
        save_catalog(seeded)
        return load_catalog()
    return data


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

st.markdown(
    """
<style>
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatAvatarIcon-user"] { display: none !important; }
[data-testid="stSidebar"] [data-testid="stSegmentedControl"],
[data-testid="stSidebar"] [data-testid="stSegmentedControl"] > div {
  width: 100% !important;
}
[data-testid="stSidebar"] [data-testid="stSegmentedControl"] button {
  flex: 1 1 0 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

if LOGO.is_file():
    st.logo(str(LOGO), size="large")

catalog = seed_catalog()
proyectos = catalog.get("proyectos") or []
cfg = load_cfg()
saved_agents = cfg.get("agents") or ["grok", "codex"]

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Proyecto")
    if proyectos:
        names = [p.get("nombre") or p.get("id") for p in proyectos]
        choice = st.selectbox("Origen", names)
        proyecto = proyectos[names.index(choice)]
    else:
        proyecto = None
        st.info("Agrega un proyecto para chatear.")

    with st.expander("Agregar proyecto"):
        nueva_ruta = st.text_input("Carpeta del proyecto")
        nuevo_nombre = st.text_input("Nombre (opcional)", placeholder="Mi app")
        if st.button("Indexar y empaquetar", type="primary"):
            if not nueva_ruta.strip():
                st.error("Indica una ruta.")
            else:
                try:
                    with st.status("CodeGraph + Repomix", expanded=True) as status:
                        entry = add_project(nueva_ruta, nuevo_nombre)
                        status.update(label="Proyecto listo", state="complete")
                    st.success(f"Agregado: {entry['nombre']}")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    st.subheader("Modo de ejecución")
    modo = st.segmented_control(
        "Modo",
        options=["CLI local", "API key"],
        default="CLI local",
        label_visibility="collapsed",
        width="stretch",
    )

    st.subheader("Motor")
    if modo == "CLI local":
        clis = [a for a in ("grok", "codex") if a in saved_agents] or ["grok", "codex"]
        motor = st.selectbox("CLI", clis)
        modelos = GROK_MODELS if motor == "grok" else CODEX_MODELS
        st.caption("Sesión de esta PC. Sin API keys.")
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
    year = datetime.now().year
    if SIPI.is_file():
        sipi_b64 = __import__("base64").b64encode(SIPI.read_bytes()).decode("ascii")
        sipi_img = f'<img src="data:image/png;base64,{sipi_b64}" width="56" alt="Sipi" />'
    else:
        sipi_img = ""
    st.markdown(
        f"""
<div style="text-align:center;padding:0.5rem 0 0.25rem;">
  {sipi_img}
  <div style="font-weight:600;margin-top:0.35rem;">Sipi</div>
  <div style="color:#6b7280;font-size:0.8rem;">Asistente de soporte · Sipecom</div>
  <div style="color:#9ca3af;font-size:0.75rem;margin-top:0.2rem;">© {year}</div>
</div>
""",
        unsafe_allow_html=True,
    )

if not proyecto:
    st.info("Agrega un proyecto en la barra lateral. Python corre CodeGraph y Repomix al registrarlo.")
    st.stop()

for item in st.session_state.messages:
    if item["role"] == "user":
        if item.get("content"):
            st.markdown(item["content"])
        for path in item.get("adjuntos") or []:
            p = Path(path)
            if p.suffix.lower() in IMAGE_EXT and p.is_file():
                st.image(str(p), caption=p.name)
        continue
    kwargs = {"avatar": str(SIPI)} if SIPI.is_file() else {}
    with st.chat_message("assistant", **kwargs):
        if item.get("content"):
            st.markdown(item["content"])
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
        st.markdown(answer)
        if used:
            st.caption(f"motor: `{used}`")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "motor": used, "command": cmd}
    )

"""Consola SIPECOM-SOPORTE. Chat nativo Streamlit (chat_input + sidebar)."""
from __future__ import annotations

import importlib
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml

from soporte_sipecom.config import DEFAULT_PORT, load as load_cfg, save as save_cfg
from soporte_sipecom.constants import VALID_AGENTS
from soporte_sipecom.detect import probe_archify, probe_codegraph, probe_repomix, which
from soporte_sipecom.ingest import add_project, load_catalog, save_catalog
from soporte_sipecom.onboard import HINTS, detected_agents, probe_node, probe_npm
import soporte_sipecom.detect as _detect_mod
import soporte_sipecom.models as _models_mod
import soporte_sipecom.engine as _engine_mod

importlib.reload(_detect_mod)
_models_mod = importlib.reload(_models_mod)
_engine_mod = importlib.reload(_engine_mod)
run_engine = _engine_mod.run_engine
baked_effort = _models_mod.baked_effort
list_efforts = _models_mod.list_efforts
list_models = _models_mod.list_models

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
API_PROVIDERS = ["OpenAI", "xAI (Grok)", "Anthropic (Claude)"]
SIPI = ASSETS / "sipi-colibri.png"
LOGO = ASSETS / "sipecom-logo.png"


def pick_folder() -> str:
    """Explorador nativo de carpetas (solo tiene sentido en localhost)."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        chosen = filedialog.askdirectory(title="Carpeta del proyecto")
        root.destroy()
        return chosen or ""
    except Exception:
        return ""


def seed_catalog() -> dict:
    return load_catalog()


def chat_dir() -> Path:
    sid = st.session_state.setdefault("chat_id", str(int(time.time() * 1000)))
    path = Path.home() / ".soporte-sipecom" / "chats" / str(sid)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_uploads(files) -> list[Path]:
    if not files:
        return []
    dest = chat_dir()
    paths: list[Path] = []
    for uploaded in files:
        name = Path(getattr(uploaded, "name", "archivo")).name or "archivo"
        path = dest / f"{int(time.time() * 1000)}-{name}"
        path.write_bytes(uploaded.getvalue())
        paths.append(path)
    return paths


@st.cache_data(ttl=90, show_spinner=False)
def cached_tools():
    rows = [probe_node(), probe_npm(), probe_codegraph(), probe_repomix(), probe_archify()]
    return [(p.name, bool(p.ok), p.version or "", HINTS.get(p.name) or p.detail or "") for p in rows]


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
live_agents = detected_agents()
if live_agents and cfg.get("agents") != live_agents:
    cfg["agents"] = live_agents
    save_cfg(cfg)
saved_agents = cfg.get("agents") or live_agents

if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_images" not in st.session_state:
    st.session_state.conversation_images = []

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
        if st.session_state.pop("clear_ruta", False):
            st.session_state.nueva_ruta = ""
        if "picked_folder" in st.session_state:
            st.session_state.nueva_ruta = st.session_state.pop("picked_folder")
        ruta_col, btn_col = st.columns([4, 1], vertical_alignment="bottom")
        with ruta_col:
            nueva_ruta = st.text_input("Carpeta del proyecto", key="nueva_ruta")
        with btn_col:
            if st.button("Examinar", width="stretch"):
                chosen = pick_folder()
                if chosen:
                    st.session_state.picked_folder = chosen
                    st.rerun()
        nuevo_nombre = st.text_input("Nombre (opcional)", placeholder="Mi app")
        if st.button("Indexar y empaquetar", type="primary"):
            if not (nueva_ruta or "").strip():
                st.error("Elige una carpeta.")
            else:
                try:
                    with st.status("CodeGraph + Repomix", expanded=True) as status:
                        entry = add_project(nueva_ruta, nuevo_nombre)
                        status.update(label="Proyecto listo", state="complete")
                    st.success(f"Agregado: {entry['nombre']}")
                    st.session_state.clear_ruta = True
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    tools = cached_tools()
    tools_ok = all(ok for _, ok, _, _ in tools)
    with st.expander("Herramientas", expanded=not tools_ok):
        for name, ok, ver, hint in tools:
            st.caption(f"{'OK' if ok else 'NO'}  {name}" + (f"  {ver}" if ver else ""))
            if not ok and hint:
                st.caption(hint)
        st.caption("CodeGraph + Repomix = contexto del proyecto (sin volcar el pack).")

    if st.button("Nueva conversación"):
        st.session_state.messages = []
        st.session_state.conversation_images = []
        st.session_state.chat_id = str(int(time.time() * 1000))
        st.rerun()

    conv_imgs = [Path(p) for p in st.session_state.conversation_images if Path(p).is_file()]
    if conv_imgs:
        with st.expander(f"Imágenes de esta conversación ({len(conv_imgs)})", expanded=False):
            for p in conv_imgs:
                st.image(str(p), caption=p.name, width=120)

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
        clis = list(VALID_AGENTS)
        preferred = cfg.get("last_agent") if cfg.get("last_agent") in clis else None
        if not preferred:
            preferred = next((a for a in live_agents if a in clis), clis[0])
        motor = st.selectbox("CLI", clis, index=clis.index(preferred), key="cli_agent")
        if motor and motor != cfg.get("last_agent"):
            cfg["last_agent"] = motor
            cfg["agents"] = live_agents or list(VALID_AGENTS)
            save_cfg(cfg)
        if not which(motor):
            st.caption(f"{motor} no está en esta PC. El resto de CLIs sí se pueden elegir.")
        else:
            st.caption("Sesión local. Modelos = listado vivo de esa CLI.")
        rows = list_models(motor)
        ids = [m.id for m in rows]
        labels = {
            m.id: (f"{m.label} ({m.id})" if m.label and m.label != m.id else m.id)
            for m in rows
        }
        if ids:
            default_id = next((m.id for m in rows if m.default), ids[0])
            modelo = st.selectbox(
                "Modelo",
                ids,
                index=ids.index(default_id) if default_id in ids else 0,
                format_func=lambda mid: labels.get(mid, mid),
                key=f"cli_model_{motor}",
            )
            efforts = list_efforts(motor, modelo, rows)
            if efforts:
                effort_idx = efforts.index("medium") if "medium" in efforts else 0
                effort = st.selectbox(
                    "Effort",
                    efforts,
                    index=effort_idx,
                    key=f"cli_effort_{motor}_{modelo}",
                )
            else:
                effort = baked_effort(modelo) or ""
                if effort:
                    st.caption(f"Effort ya va en el modelo (`{effort}`).")
        else:
            modelo = ""
            effort = "medium"
            st.warning("Esta CLI no devolvió modelos. Revisa instalación o `sipecom-soporte models`.")
    else:
        motor = "grok"
        st.selectbox("Proveedor", API_PROVIDERS)
        st.text_input("API key", type="password", placeholder="sk-…")
        modelo = st.text_input("Modelo", placeholder="id de modelo")
        effort = st.selectbox("Effort", ["low", "medium", "high", "xhigh"], index=1)
        st.caption("La key no se guarda en disco.")

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
    for p in adjuntos:
        sp = str(p)
        if sp not in st.session_state.conversation_images:
            st.session_state.conversation_images.append(sp)
    memoria = [Path(p) for p in st.session_state.conversation_images if Path(p).is_file()]

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
                    memoria,
                    int(catalog.get("timeout_s") or 240),
                )
            status.update(label="Listo", state="complete")
        st.markdown(answer)
        if used:
            st.caption(f"motor: `{used}`")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "motor": used, "command": cmd}
    )

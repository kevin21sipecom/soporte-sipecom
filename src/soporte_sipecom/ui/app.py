"""Consola SIPECOM-SOPORTE. Chat nativo Streamlit (chat_input + sidebar)."""
from __future__ import annotations

import importlib
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml

from soporte_sipecom.config import DEFAULT_PORT, load as load_cfg, save as save_cfg
from soporte_sipecom.conversations import load_index, load_thread, new_id, save_thread, thread_dir
from soporte_sipecom.ingest import add_project, load_catalog, save_catalog
from soporte_sipecom.onboard import detected_agents
from soporte_sipecom.tokens import format_int, thread_usage
import soporte_sipecom.detect as _detect_mod
import soporte_sipecom.models as _models_mod
import soporte_sipecom.engine as _engine_mod
import soporte_sipecom.maps as _maps_mod

importlib.reload(_detect_mod)
_models_mod = importlib.reload(_models_mod)
_engine_mod = importlib.reload(_engine_mod)
_maps_mod = importlib.reload(_maps_mod)
run_engine = _engine_mod.run_engine
baked_effort = _models_mod.baked_effort
list_efforts = _models_mod.list_efforts
list_models = _models_mod.list_models
existing_artifacts = _maps_mod.existing_artifacts
prepare_embed = _maps_mod.prepare_embed
render_mapa = _maps_mod.render_mapa

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
    sid = st.session_state.setdefault("chat_id", new_id())
    return thread_dir(str(sid))


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


def persist_chat(project_id: str = "") -> None:
    save_thread(
        st.session_state.chat_id,
        st.session_state.messages,
        st.session_state.conversation_images,
        project_id,
        st.session_state.get("intake") or "",
    )


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
.st-key-sipe_index,
[class*="st-key-sipe_index"] {
  position: fixed !important;
  right: 6px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  width: 6px !important;
  max-width: 6px !important;
  z-index: 60;
  height: auto !important;
  min-height: 0 !important;
}
.st-key-sipe_index [data-testid="stVerticalBlock"],
[class*="st-key-sipe_index"] [data-testid="stVerticalBlock"] {
  gap: 0.18rem !important;
}
.st-key-sipe_index *,
[class*="st-key-sipe_index"] *,
[class*="st-key-rail"] {
  min-height: 0 !important;
  min-width: 0 !important;
}
.st-key-sipe_index button,
[class*="st-key-sipe_index"] button,
[class*="st-key-rail"] button {
  width: 2px !important;
  max-width: 2px !important;
  min-width: 2px !important;
  height: 7px !important;
  max-height: 7px !important;
  min-height: 7px !important;
  padding: 0 !important;
  margin: 0 auto !important;
  border: 0 !important;
  border-radius: 1px !important;
  background: #b4bac6 !important;
  opacity: 0.55 !important;
  box-shadow: none !important;
  font-size: 0 !important;
  line-height: 0 !important;
  color: transparent !important;
}
.st-key-sipe_index button p,
.st-key-sipe_index button span,
[class*="st-key-sipe_index"] button p,
[class*="st-key-sipe_index"] button span {
  display: none !important;
}
.st-key-sipe_index button:hover,
[class*="st-key-sipe_index"] button:hover {
  opacity: 0.95 !important;
  background: #8b93a3 !important;
}
.st-key-sipe_index button[kind="primary"],
[class*="st-key-sipe_index"] button[kind="primary"] {
  background: #5b6ee8 !important;
  opacity: 1 !important;
  height: 9px !important;
  max-height: 9px !important;
  min-height: 9px !important;
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

if "chat_id" not in st.session_state:
    existing = load_index()
    if existing:
        st.session_state.chat_id = existing[0]["id"]
        msgs, imgs, intake = load_thread(existing[0]["id"])
        st.session_state.messages = msgs
        st.session_state.conversation_images = imgs
        st.session_state.intake = intake
    else:
        st.session_state.chat_id = new_id()
        st.session_state.messages = []
        st.session_state.conversation_images = []
        st.session_state.intake = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_images" not in st.session_state:
    st.session_state.conversation_images = []
if "intake" not in st.session_state:
    st.session_state.intake = ""

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

    conv_imgs = [Path(p) for p in st.session_state.conversation_images if Path(p).is_file()]
    if conv_imgs:
        with st.expander(f"Imágenes de esta conversación ({len(conv_imgs)})", expanded=False):
            for p in conv_imgs:
                st.image(str(p), caption=p.name, width=120)

    st.subheader("Error de la app")
    st.caption("Pega el texto rojo, el stack o el log. No es el chat: el chat es tu pregunta. Esto ancla la búsqueda en el código.")
    st.text_area(
        "Error / log / stack",
        key="intake",
        height=120,
        placeholder="Exception, stack trace, log…",
        label_visibility="collapsed",
    )

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
        clis = list(live_agents)
        if not clis:
            st.warning("No hay grok, antigravity ni codex en esta PC.")
            motor = ""
            modelo = ""
            effort = "medium"
        else:
            preferred = cfg.get("last_agent") if cfg.get("last_agent") in clis else clis[0]
            motor = st.selectbox("CLI", clis, index=clis.index(preferred), key="cli_agent")
            if motor and motor != cfg.get("last_agent"):
                cfg["last_agent"] = motor
                cfg["agents"] = clis
                save_cfg(cfg)
            if len(clis) == 1:
                st.caption(f"Única CLI detectada: `{motor}`.")
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

pid = (proyecto or {}).get("id") or ""
has_user = any(
    (m.get("role") == "user") and (m.get("content") or "").strip()
    for m in st.session_state.get("messages") or []
)
with st.container(key="sipe_index"):
    if st.button(
        "\u200b",
        help="Nueva conversación",
        key="rail_new",
        type="primary" if not has_user else "secondary",
    ):
        persist_chat(pid)
        st.session_state.chat_id = new_id()
        st.session_state.messages = []
        st.session_state.conversation_images = []
        st.session_state.jump_to = None
        st.session_state.intake = ""
        st.rerun()
    seen_ids: set[str] = set()
    for item in load_index()[:24]:
        cid = item.get("id") or ""
        if not cid or cid in seen_ids:
            continue
        seen_ids.add(cid)
        title = item.get("title") or "Nueva conversación"
        if cid == st.session_state.chat_id and not has_user:
            continue
        if title == "Nueva conversación" and cid != st.session_state.chat_id:
            continue
        active = cid == st.session_state.chat_id
        if st.button(
            "\u200b",
            help=title,
            key=f"rail_{cid}",
            type="primary" if active else "secondary",
        ):
            if cid != st.session_state.chat_id:
                persist_chat(pid)
                msgs, imgs, intake = load_thread(cid)
                st.session_state.chat_id = cid
                st.session_state.messages = msgs
                st.session_state.conversation_images = imgs
                st.session_state.intake = intake
                st.session_state.jump_to = None
                st.rerun()

if not proyecto:
    st.info("Agrega un proyecto en la barra lateral. Python corre CodeGraph y Repomix al registrarlo.")
    st.stop()

if True:
    vista = st.segmented_control(
        "Vista",
        options=["Chat", "Mapa"],
        default="Chat",
        key="vista_principal",
        label_visibility="collapsed",
    )
    if not vista:
        vista = "Chat"

    tin, tout, total = thread_usage(st.session_state.messages)
    st.caption(
        f"Este hilo · {format_int(total)} tokens "
        f"(entrada {format_int(tin)} · salida {format_int(tout)}). "
        "Estimado · 4 caracteres ≈ 1 token. CLI local: no es factura de API."
    )

    if vista == "Mapa":
        st.subheader("Mapa")
        st.caption("Archify a partir de CodeGraph + pack. Sin inventar topología.")
        arts = existing_artifacts(proyecto)
        pngs = [p for p in arts if p.suffix.lower() in {".png", ".webp"}]
        htmls = [p for p in arts if p.suffix.lower() == ".html"]
        if htmls:
            import streamlit.components.v1 as components

            raw = prepare_embed(htmls[0].read_text(encoding="utf-8", errors="replace"))
            components.html(raw, height=640, scrolling=False)
        elif pngs:
            st.image(str(pngs[0]), use_container_width=True)
        else:
            st.info("Todavía no hay mapa de este proyecto.")
        if st.button("Armar mapa", type="primary"):
            try:
                with st.status("CodeGraph + Archify", expanded=True) as status:
                    result = render_mapa(proyecto)
                    status.update(label="Mapa listo", state="complete")
                catalog = load_catalog()
                for item in catalog.get("proyectos") or []:
                    if item.get("id") == proyecto.get("id"):
                        item["mapa_html"] = result.get("html")
                        if result.get("png"):
                            item["mapa_png"] = result["png"]
                save_catalog(catalog)
                st.rerun()
            except Exception as exc:
                st.error(str(exc)[:400])
        st.stop()

    jump = st.session_state.get("jump_to")
    for idx, item in enumerate(st.session_state.messages):
        highlight = jump is not None and idx == jump
        box = st.container(border=highlight)
        with box:
            if highlight:
                st.caption(f"Pregunta #{idx + 1}")
            if item["role"] == "user":
                if item.get("content"):
                    st.markdown(item["content"])
                if (item.get("incidente") or "").strip():
                    with st.expander("Error pegado", expanded=False):
                        st.code(item["incidente"][:4000])
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
                tin_m = int(item.get("tokens_in") or 0)
                tout_m = int(item.get("tokens_out") or 0)
                if tin_m or tout_m:
                    st.caption(f"tokens: {format_int(tin_m)} in · {format_int(tout_m)} out")

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

    incidente = (st.session_state.get("intake") or "").strip()
    st.session_state.messages.append(
        {
            "role": "user",
            "content": text,
            "adjuntos": [str(p) for p in adjuntos],
            "incidente": incidente,
        }
    )
    if text:
        st.markdown(text)
    for p in adjuntos:
        if p.suffix.lower() in IMAGE_EXT:
            st.image(str(p), caption=p.name)

    with st.chat_message("assistant", avatar=str(SIPI) if SIPI.is_file() else None):
        with st.status(":shimmer[Escribiendo]", type="compact") as status:
            if modo != "CLI local":
                answer, used, cmd, usage = (
                    "Modo API key: aún no ejecuta remoto. Cambia a CLI local.",
                    "none",
                    "",
                    {"tokens_in": 0, "tokens_out": 0},
                )
            else:
                answer, used, cmd, usage = run_engine(
                    motor,
                    modelo,
                    effort,
                    proyecto,
                    text,
                    memoria,
                    int(catalog.get("timeout_s") or 240),
                    incidente,
                )
            status.update(label="Listo", state="complete")
        st.markdown(answer)
        if used:
            st.caption(f"motor: `{used}`")
        tin_m = int((usage or {}).get("tokens_in") or 0)
        tout_m = int((usage or {}).get("tokens_out") or 0)
        if tin_m or tout_m:
            st.caption(f"tokens: {format_int(tin_m)} in · {format_int(tout_m)} out")

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "motor": used,
            "command": cmd,
            "tokens_in": int((usage or {}).get("tokens_in") or 0),
            "tokens_out": int((usage or {}).get("tokens_out") or 0),
        }
    )
    save_thread(
        st.session_state.chat_id,
        st.session_state.messages,
        st.session_state.conversation_images,
        (proyecto or {}).get("id") or "",
        st.session_state.get("intake") or "",
    )

"""Consola Streamlit SIPECOM-SOPORTE — diseño del chatbot."""
from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml

from soporte_sipecom.config import DEFAULT_PORT, load as load_cfg
from soporte_sipecom.detect import which
from soporte_sipecom.engine import run_engine

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
STYLES = HERE / "styles.css"
DEFAULT_CATALOGO = Path(
    r"C:/Users/kfernandez/projects/seguridad/prueba del desposte/salida/chef/catalogo.yaml"
)
UPLOADS = HERE / ".uploads"
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
GROK_MODELS = ["grok-4.6", "grok-4.5"]
CODEX_MODELS = ["gpt-6-astra"]
EFFORTS = ["low", "medium", "high", "xhigh"]


def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


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


def inject_chrome() -> None:
    css = STYLES.read_text(encoding="utf-8") if STYLES.is_file() else ""
    logo = ASSETS / "sipecom-logo.jpg"
    logo_src = f"data:image/jpeg;base64,{_b64(logo)}" if logo.is_file() else ""
    st.markdown(
        f"""
<style>{css}</style>
<div class="sipe-header">
  <div class="sipe-brand">
    <div class="sipe-logo-wrap"><img src="{logo_src}" alt="Sipecom" /></div>
    <span class="sipe-title-muted">Consola de Soporte</span>
  </div>
  <div class="sipe-pill"><span class="sipe-dot"></span> CLI local activo</div>
</div>
""",
        unsafe_allow_html=True,
    )


def footer() -> None:
    sipi = ASSETS / "sipi-colibri.png"
    src = f"data:image/png;base64,{_b64(sipi)}" if sipi.is_file() else ""
    year = datetime.now().year
    st.markdown(
        f"""
<div class="sipe-footer">
  <div class="sipe-sipi">
    <img src="{src}" alt="Sipi" />
    <div><strong>Sipi</strong><span>Asistente de soporte · Sipecom</span></div>
  </div>
  <p>© {year} Sipecom · Ejecución local, sin API keys · puerto {DEFAULT_PORT}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def save_uploads(files) -> list[Path]:
    if not files:
        return []
    UPLOADS.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS / str(int(__import__("time").time() * 1000))
    dest.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for uploaded in files:
        name = Path(getattr(uploaded, "name", "archivo")).name or "archivo"
        path = dest / name
        path.write_bytes(uploaded.getvalue())
        paths.append(path)
    return paths


def main() -> None:
    st.set_page_config(
        page_title="SIPECOM-SOPORTE · Chef",
        page_icon=str(ASSETS / "sipi-colibri.png") if (ASSETS / "sipi-colibri.png").is_file() else "🦜",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_chrome()
    catalog = load_catalog()
    proyectos = catalog.get("proyectos") or []
    cfg = load_cfg()
    saved_agents = cfg.get("agents") or ["grok", "codex"]

    if not proyectos:
        st.warning("No hay catalogo.yaml. Corre un desposte o define SOPORTE_CATALOGO.")
        footer()
        return

    names = [p.get("nombre") or p.get("id") for p in proyectos]
    with st.sidebar:
        st.markdown("**Proyecto**")
        choice = st.selectbox("Origen", names, label_visibility="visible")
        proyecto = proyectos[names.index(choice)]
        st.divider()
        st.markdown("**Motor**")
        clis = [a for a in ("grok", "codex") if a in saved_agents] or ["grok", "codex"]
        motor = st.selectbox("CLI", clis)
        modelos = GROK_MODELS if motor == "grok" else CODEX_MODELS
        modelo = st.selectbox("Modelo", modelos)
        extra = st.text_input("Modelo extra (opcional)", placeholder="id de modelo")
        if extra.strip():
            modelo = extra.strip()
        effort = st.selectbox("Effort", EFFORTS, index=EFFORTS.index("medium"))
        st.caption("Sesión de esta PC. Sin API keys.")
        st.code(which("codex") or "codex: no encontrado", language=None)
        st.code(which("grok") or "grok: no encontrado", language=None)
        st.caption(f"origen: {proyecto.get('origen', '')}")
        mapa = Path(proyecto.get("mapa") or "")
        if mapa.is_file() and "pendiente" in mapa.read_text(encoding="utf-8", errors="replace").lower():
            st.warning("El MAPA declara pendientes: no afirmes cobertura total.")

    st.markdown("## Chef de desposte")
    st.caption("CLI local: `codex exec` o `grok --prompt-file`. Sin API keys.")

    tab_term, tab_mapas, tab_receta = st.tabs(["Terminal", "Mapas", "Receta"])

    with tab_mapas:
        mapas = Path(proyecto.get("mapas") or "")
        pngs = sorted(mapas.glob("*1440x900.dark.png")) if mapas.is_dir() else []
        if not pngs:
            st.info("Los módulos declarados en MAPA.md aparecen aquí. El mapa puede tener pendientes.")
        for img in pngs:
            st.subheader(img.name.replace(".visual-check.1440x900.dark.png", ""))
            st.image(str(img), width="stretch")

    with tab_receta:
        receta = Path(proyecto.get("receta") or "")
        if receta.is_file():
            st.markdown(receta.read_text(encoding="utf-8", errors="replace"))
        else:
            st.info("RECETA.md describe el corte cuando el camino es mapa. En multi-desposte puede no existir.")

    with tab_term:
        st.caption("Consultas con `codex exec` o `grok --prompt-file` de esta máquina. Texto e imágenes.")
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for item in st.session_state.messages:
            with st.chat_message(item["role"]):
                if item.get("command"):
                    st.code(item["command"], language="bash")
                text = item.get("content") or ""
                if text:
                    st.markdown(text)
                for path in item.get("adjuntos") or []:
                    p = Path(path)
                    if p.suffix.lower() in IMAGE_EXT and p.is_file():
                        st.image(str(p), caption=p.name, width="stretch")
                if item.get("motor"):
                    st.caption(f"motor: {item['motor']}")

        user_in = st.chat_input(
            "Texto y/o imágenes (como en un terminal)",
            accept_file="multiple",
            file_type=["png", "jpg", "jpeg", "webp", "gif", "txt", "md"],
        )
        if user_in:
            text = user_in.text if hasattr(user_in, "text") else str(user_in)
            incoming = list(getattr(user_in, "files", None) or [])
            adjuntos = save_uploads(incoming)
            st.session_state.messages.append(
                {"role": "user", "content": text or "", "adjuntos": [str(p) for p in adjuntos]}
            )
            with st.chat_message("user"):
                if text:
                    st.markdown(text)
                for p in adjuntos:
                    if p.suffix.lower() in IMAGE_EXT:
                        st.image(str(p), caption=p.name, width="stretch")
            with st.chat_message("assistant"):
                with st.spinner("Lanzando CLI local…"):
                    answer, used, cmd = run_engine(
                        motor,
                        modelo,
                        effort,
                        proyecto,
                        text or "",
                        adjuntos,
                        int(catalog.get("timeout_s") or 240),
                    )
                if cmd:
                    st.code(cmd, language="bash")
                st.markdown(answer)
                if used:
                    st.caption(f"motor: {used}")
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "motor": used, "command": cmd}
            )

    footer()


if __name__ == "__main__":
    main()

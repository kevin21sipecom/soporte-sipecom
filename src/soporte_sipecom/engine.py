"""Lanzar Codex/Grok locales. Sin API keys."""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from soporte_sipecom.detect import which

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
API_KEY_NAMES = {
    "OPENAI_API_KEY",
    "OPENAI_API_KEY_CODEX",
    "XAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GROK_API_KEY",
}


def cli_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key in API_KEY_NAMES or key.endswith("_API_KEY"):
            env.pop(key, None)
    extras = []
    for name in ("grok", "codex"):
        path = which(name)
        if path:
            extras.append(str(Path(path).parent))
    if extras:
        env["PATH"] = os.pathsep.join(extras + [env.get("PATH", "")])
    return env


def read_capped(path: str, limit: int = 50000) -> str:
    p = Path(path) if path else Path()
    if not path or not p.is_file():
        return f"(no hay archivo: {path or '—'})"
    text = p.read_text(encoding="utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit] + f"\n\n… truncado ({len(text)} chars). El resto está en {p}."
    return text


def origen_readme(origen: str) -> str:
    root = Path(origen) if origen else Path()
    if not root.is_dir():
        return "(origen ilegible)"
    chunks: list[str] = []
    for name in ("AGENTS.md", "README.md", "INSTRUCCIONES.md", "INSTRUCCIONES-LEGACY.md"):
        candidate = root / name
        if candidate.is_file():
            chunks.append(f"## {name}\n{read_capped(str(candidate), 20000)}")
    return "\n\n".join(chunks) or "(sin README/AGENTS en origen)"


def build_prompt(proyecto: dict, pregunta: str, adjuntos: list[Path]) -> str:
    mapa = proyecto.get("mapa") or ""
    receta = proyecto.get("receta") or ""
    pack = proyecto.get("pack") or ""
    origen = proyecto.get("origen") or ""
    mapas = proyecto.get("mapas") or ""
    adj = "\n".join(f"- {p}" for p in adjuntos) or "(ninguno)"
    return f"""Responde en español sobre el proyecto. Eres el chef: conoces el corte y el código.
No modifiques archivos, no ejecutes migraciones, no inventes endpoints ni UX.
Si no está en el material de abajo, el pack o el origen, di que no está.
Cita archivo:línea o IDs. Usa herramientas del CLI para leer más archivos. Sin API keys.

Origen (código, lee lo que haga falta): {origen}
Pack Repomix (búsqueda en todo el repo; NO lo vuelques): {pack}
MAPA.md (puede no existir en multi-desposte): {mapa or "—"}
RECETA.md: {receta or "—"}
Diagramas: {mapas or "—"}

Adjuntos de esta consulta:
{adj}

--- README / AGENTS del origen ---
{origen_readme(origen)}

--- MAPA.md ---
{read_capped(mapa)}

--- RECETA.md ---
{read_capped(receta)}

Pregunta / texto:
{pregunta or "(sin texto; interpreta los adjuntos)"}
"""


def format_cmd(cmd: list[str]) -> str:
    parts = []
    for item in cmd:
        if " " in item or any(ch in item for ch in "\\'\""):
            parts.append('"' + item.replace('"', '\\"') + '"')
        else:
            parts.append(item)
    return " ".join(parts)


def run_engine(
    engine: str,
    model: str,
    effort: str,
    proyecto: dict,
    pregunta: str,
    adjuntos: list[Path],
    timeout_s: int = 240,
) -> tuple[str, str, str]:
    prompt = build_prompt(proyecto, pregunta, adjuntos)
    origen = proyecto.get("origen") or str(Path.home())
    grok = which("grok")
    codex = which("codex")
    images = [p for p in adjuntos if p.suffix.lower() in IMAGE_EXT]
    errors: list[str] = []
    shown_cmd = ""
    env = cli_env()
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(prompt)
        prompt_path = handle.name
    try:
        name = engine
        if name == "grok":
            if not grok:
                return "grok no está en PATH", "none", ""
            cmd = [
                grok,
                "--prompt-file",
                prompt_path,
                "-m",
                model,
                "--reasoning-effort",
                effort,
                "--output-format",
                "plain",
                "--permission-mode",
                "bypassPermissions",
                "--disable-web-search",
                "--max-turns",
                "10",
                "--cwd",
                origen,
            ]
        else:
            if not codex:
                return "codex no está en PATH", "none", ""
            cmd = [
                codex,
                "exec",
                "--skip-git-repo-check",
                "-m",
                model,
                "-c",
                f"model_reasoning_effort={effort}",
                "--sandbox",
                "danger-full-access",
            ]
            for img in images:
                cmd.extend(["-i", str(img)])
            cmd.append(
                "Responde en español. No modifiques archivos. "
                f"Lee y sigue el prompt en: {prompt_path}"
            )
        shown_cmd = format_cmd(cmd)
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                cwd=origen,
                encoding="utf-8",
                errors="replace",
                env=env,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            return f"{name} timeout {timeout_s}s", "none", shown_cmd
        except OSError as exc:
            return f"{name}: {exc}", "none", shown_cmd
        out = (completed.stdout or "").strip()
        err = (completed.stderr or "").strip()
        if completed.returncode == 0 and out:
            return out, name, shown_cmd
        return f"{name} exit {completed.returncode}: {err or out or 'sin salida'}", "none", shown_cmd
    finally:
        try:
            os.unlink(prompt_path)
        except OSError:
            pass

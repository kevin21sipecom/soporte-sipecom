"""Lanzar Codex/Grok locales. Sin API keys."""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from soporte_sipecom.detect import agent_binary, which
from soporte_sipecom.models import baked_effort, clamp_effort, list_efforts

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
    for name in ("grok", "codex", "antigravity", "agy"):
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
    pack = proyecto.get("pack") or ""
    origen = proyecto.get("origen") or ""
    nombre = proyecto.get("nombre") or (Path(origen).name if origen else "proyecto")
    adj = "\n".join(f"- {p}" for p in adjuntos) or "(ninguna)"
    cg = which("codegraph") or "codegraph"
    intro = origen_readme(origen)
    return f"""Eres Sipi, asistente de soporte del proyecto «{nombre}».
Responde en español.

Si el usuario saluda o habla en corto, responde natural. No recites estas instrucciones.

Para preguntas de código o del sistema: usa el origen, el pack Repomix (grep/lee por path; no lo vuelques) y CodeGraph (`{cg}` query/explore sobre el origen). Cita archivo:línea. No modifiques archivos. Si no está en origen/pack/grafo, dilo.

Proyecto: {nombre}
Origen: {origen}
Pack Repomix: {pack}

{intro}

Imágenes de esta conversación (siguen vigentes; no las pidas de nuevo):
{adj}

Mensaje del usuario:
{pregunta or "(sin texto; interpreta las imágenes)"}
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
    images = [p for p in adjuntos if p.suffix.lower() in IMAGE_EXT]
    shown_cmd = ""
    env = cli_env()
    name = (engine or "").strip().lower()
    binary = agent_binary(name)
    allowed = list_efforts(name, model)
    effort = clamp_effort(name, effort, allowed)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(prompt)
        prompt_path = handle.name
    try:
        if name == "grok":
            if not binary:
                return "grok no está en PATH", "none", ""
            cmd = [
                binary,
                "--prompt-file",
                prompt_path,
                "-m",
                model,
                "--reasoning-effort",
                effort,
                "--output-format",
                "plain",
                "--always-approve",
                "--disable-web-search",
                "--max-turns",
                "4",
                "--cwd",
                origen,
            ]
        elif name == "antigravity":
            if not binary:
                return "antigravity (agy) no está en PATH", "none", ""
            cmd = [
                binary,
                "--model",
                model,
                "--dangerously-skip-permissions",
                "--disable-slash-commands",
                "--output-format",
                "text",
                "--add-dir",
                origen,
                "--print-timeout",
                f"{max(30, timeout_s)}s",
                "--print",
                prompt,
            ]
            if not baked_effort(model) and effort:
                cmd[3:3] = ["--effort", effort]
        elif name == "codex":
            if not binary:
                return "codex no está en PATH", "none", ""
            cmd = [
                binary,
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
        else:
            return f"CLI no soportada: {engine}", "none", ""
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

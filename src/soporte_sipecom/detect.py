"""Detectar e instalar-validar las 4 familias del desposte.

No son API keys. Cada ficha: binario, versión, headless, auth si se puede
sin abrir TUI.

1. codegraph
2. repomix
3. archify  (CLI Node dentro de la skill Hermes, no hace falta el chat)
4. agentes  (grok / antigravity / codex) — al menos uno headless
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

from soporte_sipecom.constants import AGENT_ALIASES, VALID_AGENTS

WIN = os.name == "nt"


@dataclass
class Probe:
    name: str
    family: str
    found: bool
    ok: bool
    path: str | None = None
    version: str | None = None
    headless: bool | None = None
    detail: str = ""
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        data = asdict(self)
        return data


def _home() -> Path:
    return Path.home()


def _localappdata() -> Path:
    raw = os.environ.get("LOCALAPPDATA")
    if raw:
        return Path(raw)
    return _home() / "AppData" / "Local"


def _which_one(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return str(Path(found))
    exe = f"{name}.exe" if WIN else name
    extra = [
        _home() / ".grok" / "bin" / exe,
        _home() / "AppData" / "Local" / "Programs" / "OpenAI" / "Codex" / "bin" / exe,
        _localappdata() / "agy" / "bin" / exe,
        _home() / "scoop" / "shims" / exe,
        _localappdata() / "hermes" / "node" / exe,
        _home() / ".local" / "bin" / name,
    ]
    for path in extra:
        if path.is_file():
            return str(path)
    return None


def which(name: str) -> str | None:
    for candidate in AGENT_ALIASES.get(name, (name,)):
        found = _which_one(candidate)
        if found:
            return found
    return None


def which_node() -> str | None:
    return which("node")


def run_cmd(cmd: list[str], timeout: float = 8.0) -> tuple[int | None, str]:
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            encoding="utf-8",
            errors="replace",
        )
        text = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()
        return completed.returncode, text
    except FileNotFoundError:
        return None, "not found"
    except subprocess.TimeoutExpired:
        return None, "timeout (posible TUI; no cuenta como headless)"


def first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:200]
    return ""


def probe_codegraph() -> Probe:
    path = which("codegraph")
    if not path:
        return Probe(
            "codegraph",
            "codegraph",
            False,
            False,
            detail="no está en PATH ni en Hermes node. Instala CodeGraph y reintenta.",
        )
    code, out = run_cmd([path, "--version"])
    version = first_line(out) if code == 0 else None
    ok = code == 0 and bool(version)
    return Probe(
        "codegraph",
        "codegraph",
        True,
        ok,
        path=path,
        version=version,
        headless=True,
        detail="" if ok else out[:400],
    )


def probe_repomix() -> Probe:
    path = which("repomix")
    if not path:
        return Probe(
            "repomix",
            "repomix",
            False,
            False,
            detail="no está en PATH. npm i -g repomix o usa el node de Hermes.",
        )
    code, out = run_cmd([path, "--version"])
    version = first_line(out) if code == 0 else None
    ok = code == 0 and bool(version)
    return Probe(
        "repomix",
        "repomix",
        True,
        ok,
        path=path,
        version=version,
        headless=True,
        detail="" if ok else out[:400],
    )


def archify_root() -> Path | None:
    env = os.environ.get("ARCHIFY_HOME") or os.environ.get("ARCHIFY")
    candidates: list[Path] = []
    if env:
        candidates.append(Path(env))
    hermes_skills = os.environ.get("HERMES_SKILLS")
    if hermes_skills:
        candidates.append(Path(hermes_skills) / "creative" / "archify")
    candidates.extend(
        [
            _localappdata() / "hermes" / "skills" / "creative" / "archify",
            _home() / ".hermes" / "skills" / "creative" / "archify",
        ]
    )
    which_bin = which("archify")
    if which_bin:
        # bin/archify.mjs → skill root
        p = Path(which_bin)
        if p.name.startswith("archify"):
            if p.parent.name == "bin":
                candidates.insert(0, p.parent.parent)
            else:
                candidates.insert(0, p.parent)
    for root in candidates:
        script = root / "bin" / "archify.mjs"
        if script.is_file():
            return root
    return None


def probe_archify() -> Probe:
    """Archify es un CLI Node (bin/archify.mjs), no un MCP ni un chat skill-only."""
    node = which_node()
    root = archify_root()
    if not node:
        return Probe(
            "archify",
            "archify",
            False,
            False,
            detail="node no está. Archify se valida con `node bin/archify.mjs`.",
        )
    if not root:
        return Probe(
            "archify",
            "archify",
            False,
            False,
            detail=(
                "no se encontró bin/archify.mjs. Busca HERMES_SKILLS/creative/archify "
                "o LOCALAPPDATA/hermes/skills/creative/archify. "
                "No hace falta Hermes en runtime: basta node + esa carpeta. "
                "Opcional: ARCHIFY_HOME=/ruta/al/skill"
            ),
        )
    script = root / "bin" / "archify.mjs"
    # usage sin args (rápido). doctor es más pesado; lo usamos si usage responde.
    code, out = run_cmd([node, str(script)], timeout=10)
    usage_ok = "archify" in out.lower() and "render" in out.lower()
    version = None
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            import json

            version = json.loads(pkg.read_text(encoding="utf-8")).get("version")
        except OSError:
            version = None
    extra = {"root": str(root), "script": str(script), "node": node}
    if usage_ok:
        dcode, dout = run_cmd([node, str(script), "doctor"], timeout=25)
        extra["doctor_exit"] = dcode
        extra["doctor_ok"] = dcode == 0
        ok = dcode == 0
        detail = "" if ok else first_line(dout) or "doctor falló"
        return Probe(
            "archify",
            "archify",
            True,
            ok,
            path=str(script),
            version=version,
            headless=True,
            detail=detail,
            extra=extra,
        )
    return Probe(
        "archify",
        "archify",
        True,
        False,
        path=str(script),
        version=version,
        headless=True,
        detail=first_line(out) or f"exit {code}",
        extra=extra,
    )


def probe_agent(name: str) -> Probe:
    path = which(name)
    if not path:
        return Probe(
            name,
            "agent",
            False,
            False,
            detail=f"{name} no está en PATH ni en rutas conocidas.",
        )
    code, out = run_cmd([path, "--version"], timeout=8)
    version = first_line(out) if out else None
    headless = None
    detail = ""
    extra: dict = {}
    if name == "codex":
        hcode, hout = run_cmd([path, "exec", "--help"], timeout=8)
        headless = hcode == 0 and "skip-git-repo-check" in hout
        extra["exec_help"] = hcode == 0
        if not headless:
            detail = "falta `codex exec` headless"
    elif name == "grok":
        hcode, hout = run_cmd([path, "--help"], timeout=8)
        headless = "--prompt-file" in hout
        extra["prompt_file"] = headless
        if "not authenticated" in out.lower() or "not authenticated" in hout.lower():
            extra["auth"] = "missing"
            detail = "binario ok; sesión grok login pendiente"
        if not headless:
            detail = "falta --prompt-file (headless)"
    elif name == "antigravity":
        hcode, hout = run_cmd([path, "--help"], timeout=8)
        extra["binary"] = Path(path).stem
        extra["help_ok"] = hcode == 0
        headless = "--print" in hout and "--model" in hout
        extra["print"] = "--print" in hout
        extra["models_cmd"] = "models" in hout.lower()
        if not headless:
            detail = "falta --print/--model (headless)"
    ok = code == 0 or (version is not None and "error" not in (version or "").lower())
    # grok --version can work while unauthenticated
    if name == "grok" and extra.get("auth") == "missing":
        ok = bool(path) and headless is not False
    if code not in (0, None) and not version:
        ok = False
        detail = detail or first_line(out)
    return Probe(
        name,
        "agent",
        True,
        bool(ok and (headless is not False)),
        path=path,
        version=version,
        headless=headless,
        detail=detail,
        extra=extra,
    )


def doctor() -> list[Probe]:
    agents = [probe_agent(n) for n in VALID_AGENTS]
    any_agent = any(p.ok for p in agents)
    agent_summary = Probe(
        "agentes",
        "agent",
        found=any(p.found for p in agents),
        ok=any_agent,
        detail="al menos un CLI headless (grok/antigravity/codex)"
        if any_agent
        else "ningún agente headless usable",
        extra={"members": [p.as_dict() for p in agents]},
    )
    return [
        probe_codegraph(),
        probe_repomix(),
        probe_archify(),
        agent_summary,
    ]


def all_ok(probes: list[Probe]) -> bool:
    return all(p.ok for p in probes)

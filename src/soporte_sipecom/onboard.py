"""Onboarding: runtime (node/npm) + CodeGraph/Repomix/Archify + agentes."""
from __future__ import annotations

from soporte_sipecom.constants import VALID_AGENTS
from soporte_sipecom.detect import (
    Probe,
    doctor,
    first_line,
    probe_agent,
    run_cmd,
    which,
    which_node,
)

HINTS = {
    "node": "Instala Node.js LTS (trae npm). Windows: winget install OpenJS.NodeJS.LTS — luego cierra y abre la terminal.",
    "npm": "npm viene con Node.js. Si node existe y npm no, reinstala Node.js y reabre la terminal.",
    "codegraph": "Instala el CLI CodeGraph y déjalo en PATH (o en AppData/Local/codegraph/current/bin).",
    "repomix": "Con npm: npm install -g repomix",
    "archify": "Hace falta Node.js y bin/archify.mjs (skill creative/archify o ARCHIFY_HOME).",
    "grok": "Instala Grok CLI y autentica (grok login). Binario típico: ~/.grok/bin/grok",
    "antigravity": "Instala Antigravity CLI. Binario: agy",
    "codex": "Instala OpenAI Codex CLI (codex exec debe existir).",
}


def probe_node():
    path = which_node()
    if not path:
        return Probe("node", "runtime", False, False, detail=HINTS["node"])
    code, out = run_cmd([path, "--version"])
    version = first_line(out)
    ok = code == 0 and bool(version)
    return Probe("node", "runtime", True, ok, path=path, version=version, headless=True, detail="" if ok else HINTS["node"])


def probe_npm():
    path = which("npm")
    if not path:
        node = which_node()
        detail = HINTS["npm"] if node else HINTS["node"]
        return Probe("npm", "runtime", False, False, detail=detail)
    code, out = run_cmd([path, "--version"])
    version = first_line(out)
    ok = code == 0 and bool(version)
    return Probe("npm", "runtime", True, ok, path=path, version=version, headless=True, detail="" if ok else HINTS["npm"])


def detected_agents() -> list[str]:
    return [name for name in VALID_AGENTS if probe_agent(name).ok]


def onboard_report() -> tuple[list, bool]:
    runtime = [probe_node(), probe_npm()]
    tools = doctor()
    rows = runtime + tools
    ok_tools = all(p.ok for p in tools if p.family != "agent") and any(
        p.ok for p in tools if p.name == "agentes"
    )
    # 4 familias: cg, rm, archify, agentes. node/npm son prereqs de rm/archify
    families_ok = all(p.ok for p in tools)
    return rows, families_ok


def print_onboard() -> int:
    rows, families_ok = onboard_report()
    print("\nOnboarding\n")
    current_family = None
    titles = {"runtime": "Runtime", "codegraph": "Herramientas", "repomix": "Herramientas", "archify": "Herramientas", "agent": "Agentes (el dashboard elige cuál usar)"}
    for probe in rows:
        family = probe.family
        title = titles.get(family, family)
        if title != current_family:
            print(f"{title}")
            current_family = title
        mark = "OK " if probe.ok else "NO "
        ver = probe.version or ""
        print(f"  {mark}  {probe.name:<14} {ver}")
        if not probe.ok:
            hint = HINTS.get(probe.name) or probe.detail
            if hint:
                print(f"        → {hint}")
        if probe.name == "agentes":
            for member in probe.extra.get("members") or []:
                mm = "ok" if member.get("ok") else "no"
                print(f"        [{mm}] {member.get('name')}")
                if not member.get("ok"):
                    h = HINTS.get(member.get("name") or "") or member.get("detail") or ""
                    if h:
                        print(f"              → {h}")
    print()
    if families_ok:
        print("Todo OK. Siguiente:  sipecom-soporte dashboard")
        return 0
    print("Instala lo que marca NO y vuelve a correr:  sipecom-soporte")
    print("El dashboard elige grok / antigravity / codex; no hace falta `select`.")
    return 1

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
from soporte_sipecom.install_tools import AUTO_TOOLS, ask_yes_no, install_missing

HINTS = {
    "node": "winget install OpenJS.NodeJS.LTS",
    "npm": "winget install OpenJS.NodeJS.LTS",
    "codegraph": "npm i -g @colbymchenry/codegraph",
    "repomix": "npm install -g repomix",
    "archify": "viene en el paquete sipecom-soporte (se copia al decir s)",
    "grok": "Instala Grok CLI y autentica (grok login). Binario típico: ~/.grok/bin/grok",
    "antigravity": "Instala Antigravity CLI. Binario: agy",
    "codex": "Instala OpenAI Codex CLI (codex exec debe existir).",
    "opencode": "Instala OpenCode CLI (opencode). En el dashboard solo salen modelos gratis (coste 0).",
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


def _print_rows(rows) -> None:
    print("\nOnboarding\n")
    current_family = None
    titles = {
        "runtime": "Runtime",
        "codegraph": "Herramientas",
        "repomix": "Herramientas",
        "archify": "Herramientas",
        "agent": "Agentes (el dashboard elige cuál usar)",
    }
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


def _missing_auto(rows) -> list[str]:
    missing = [p.name for p in rows if not p.ok and p.name in AUTO_TOOLS]
    npm_ok = any(p.name == "npm" and p.ok for p in rows)
    if not npm_ok:
        missing = [n for n in missing if n == "archify"]
    return missing


def _print_manual(rows) -> None:
    missing = [p.name for p in rows if not p.ok and p.name in HINTS]
    cmds = [HINTS[n] for n in missing if n in {"node", "npm", "codegraph", "repomix", "archify"}]
    seen: list[str] = []
    for cmd in cmds:
        if cmd not in seen:
            seen.append(cmd)
    if seen:
        print("Copia y pega (PowerShell normal, no Administrador):")
        print()
        for cmd in seen:
            print(f"  {cmd}")
        print()
        print("Cierra y abre la terminal. Luego:  sipecom-soporte")
    else:
        print("Instala lo que marca NO y vuelve a correr:  sipecom-soporte")


def print_onboard() -> int:
    rows, families_ok = onboard_report()
    _print_rows(rows)
    if families_ok:
        print("Todo OK. Siguiente:  sipecom-soporte dashboard")
        return 0

    auto = _missing_auto(rows)
    if auto:
        names = ", ".join(auto)
        answer = ask_yes_no(f"¿Instalar ahora {names}?")
        if answer is True:
            install_missing(auto)
            print()
            rows, families_ok = onboard_report()
            _print_rows(rows)
            if families_ok:
                print("Todo OK. Siguiente:  sipecom-soporte dashboard")
                return 0
        elif answer is False:
            print("Sin instalar. Puedes hacerlo después con los comandos de abajo.\n")

    _print_manual(rows)
    print("El dashboard elige grok / antigravity / codex / opencode; no hace falta `select`.")
    return 1

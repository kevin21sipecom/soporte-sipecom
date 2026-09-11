"""CLI principal SIPECOM-SOPORTE."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from soporte_sipecom.banner import banner
from soporte_sipecom.config import DEFAULT_PORT, config_path, load, save
from soporte_sipecom.detect import doctor, probe_agent


def _print_doctor(probes, *, as_json: bool) -> int:
    if as_json:
        print(json.dumps([p.as_dict() for p in probes], indent=2, ensure_ascii=False))
        return 0 if all(p.ok for p in probes) else 1
    width = max(len(p.name) for p in probes)
    print()
    for probe in probes:
        mark = "OK " if probe.ok else "NO "
        loc = probe.path or "—"
        ver = probe.version or ""
        print(f"  {mark}  {probe.name:<{width}}  {ver:<18} {loc}")
        if probe.detail and not probe.ok:
            print(f"        {probe.detail}")
        if probe.name == "agentes":
            for member in probe.extra.get("members") or []:
                mm = "ok" if member.get("ok") else "no"
                print(
                    f"        [{mm}] {member.get('name')}: "
                    f"{member.get('version') or ''} {member.get('path') or '—'}"
                )
                if member.get("detail") and not member.get("ok"):
                    print(f"              {member['detail']}")
    print()
    ok = all(p.ok for p in probes)
    print("4/4 listas" if ok else "faltan herramientas (4 familias: codegraph, repomix, archify, agentes)")
    return 0 if ok else 1


def _usable_agents() -> list[dict]:
    names = ("codex", "grok", "claude")
    out = []
    for name in names:
        probe = probe_agent(name)
        if probe.found:
            out.append(probe.as_dict())
    return out


def cmd_select(chosen: list[str] | None) -> int:
    found = _usable_agents()
    ok_names = [a["name"] for a in found if a.get("ok")]
    if not found:
        print("No hay agentes CLI detectados (codex, grok, claude).")
        return 1
    print("Agentes detectados:")
    for i, item in enumerate(found, 1):
        flag = "OK" if item.get("ok") else "NO"
        print(f"  {i}. [{flag}] {item['name']:8}  {item.get('version') or ''}  {item.get('path') or ''}")
    selected: list[str]
    if chosen:
        selected = []
        for name in chosen:
            name = name.strip().lower()
            if name not in {a["name"] for a in found}:
                print(f"no detectado: {name}")
                return 1
            selected.append(name)
    elif sys.stdin.isatty() and sys.stdout.isatty():
        raw = input("\nNúmeros o nombres (ej. 1,2 o grok,codex). Vacío = todos los OK: ").strip()
        if not raw:
            selected = ok_names
        else:
            selected = []
            tokens = [t.strip().lower() for t in raw.replace(";", ",").split(",") if t.strip()]
            for tok in tokens:
                if tok.isdigit():
                    idx = int(tok) - 1
                    if idx < 0 or idx >= len(found):
                        print(f"índice inválido: {tok}")
                        return 1
                    selected.append(found[idx]["name"])
                else:
                    if tok not in {a["name"] for a in found}:
                        print(f"no detectado: {tok}")
                        return 1
                    selected.append(tok)
    else:
        selected = ok_names
        print(f"(sin TTY) usando todos los OK: {', '.join(selected) or '—'}")
    cfg = load()
    cfg["agents"] = selected
    cfg["port"] = cfg.get("port") or DEFAULT_PORT
    path = save(cfg)
    print(f"guardado: {path}")
    print(f"agentes: {', '.join(selected) or '—'}")
    print(f"puerto:  {cfg['port']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="soporte",
        description="SIPECOM-SOPORTE — CLI de soporte (doctor de CLIs, puerto 2121).",
    )
    parser.add_argument("--port", type=int, default=None, help="puerto (default 2121)")
    sub = parser.add_subparsers(dest="cmd")

    doc = sub.add_parser("doctor", help="Validar codegraph, repomix, archify y agentes")
    doc.add_argument("--json", action="store_true")

    sel = sub.add_parser("select", help="Elegir agentes CLI a usar")
    sel.add_argument(
        "--use",
        default="",
        help="lista: grok,codex,claude (si se omite, pregunta o usa los OK)",
    )

    cfgp = sub.add_parser("config", help="Mostrar config (puerto + agentes)")
    sub.add_parser("ui", help="Abrir consola Streamlit (puerto 2121)")

    args = parser.parse_args(argv)
    port = args.port if args.port else load().get("port") or DEFAULT_PORT

    if args.cmd is None:
        print(banner(port))
        probes = doctor()
        code = _print_doctor(probes, as_json=False)
        print("\nSiguiente:  soporte select --use grok,codex")
        print(f"Puerto de servicio: {port}")
        return code

    if args.cmd == "doctor":
        print(banner(port))
        return _print_doctor(doctor(), as_json=args.json)

    if args.cmd == "select":
        print(banner(port))
        chosen = [x for x in args.use.split(",") if x.strip()] if args.use else None
        return cmd_select(chosen)

    if args.cmd == "config":
        print(banner(port))
        cfg = load()
        if args.port:
            cfg["port"] = args.port
            save(cfg)
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        print(f"archivo: {config_path()}")
        return 0

    if args.cmd == "ui":
        app = Path(__file__).resolve().parent / "ui" / "app.py"
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app),
            "--server.address",
            "127.0.0.1",
            "--server.port",
            str(port),
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ]
        print(banner(port))
        print(f"Streamlit → http://127.0.0.1:{port}")
        return subprocess.call(cmd)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

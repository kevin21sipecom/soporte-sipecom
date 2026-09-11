"""Registrar proyectos: CodeGraph + Repomix ejecutados desde Python."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import yaml

from soporte_sipecom.detect import which

IGNORE = (
    "**/*.dll,**/*.pdb,**/*.exe,**/*.nupkg,**/*.cache,"
    "**/bin/**,**/obj/**,**/packages/**,**/*.min.js,**/*.map,**/.vs/**"
)


def data_dir() -> Path:
    path = Path.home() / ".soporte-sipecom"
    path.mkdir(parents=True, exist_ok=True)
    return path


def catalog_path() -> Path:
    return data_dir() / "catalogo.yaml"


def packs_dir() -> Path:
    path = data_dir() / "packs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def native(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip()).strip("-").lower()
    return slug or "proyecto"


def load_catalog() -> dict:
    path = catalog_path()
    if path.is_file():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        data = {}
    data.setdefault("motor_default", "grok")
    data.setdefault("timeout_s", 240)
    data.setdefault("proyectos", [])
    return data


def save_catalog(data: dict) -> Path:
    path = catalog_path()
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def run(cmd: list[str], timeout: int) -> tuple[int, str]:
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
        encoding="utf-8",
        errors="replace",
    )
    out = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()
    return completed.returncode, out


def ensure_codegraph(origen: Path) -> str:
    cg = which("codegraph")
    if not cg:
        raise RuntimeError("codegraph no está instalado. Corre: uv run soporte doctor")
    root = native(origen)
    code, out = run([cg, "status", root, "--json"], timeout=60)
    initialized = False
    if code == 0:
        try:
            payload = json.loads(out[out.find("{") : out.rfind("}") + 1] if "{" in out else out)
            initialized = bool(payload.get("initialized"))
        except json.JSONDecodeError:
            initialized = "initialized" in out.lower() and "true" in out.lower()
    if not initialized:
        code, out = run([cg, "init", root, "--yes"], timeout=600)
        if code != 0:
            raise RuntimeError(f"codegraph init falló:\n{out[-2000:]}")
        return "codegraph init"
    pending = False
    if '"pendingChanges"' in out or "pending" in out.lower():
        pending = True
    if pending:
        code, out = run([cg, "sync", root], timeout=180)
        if code != 0:
            raise RuntimeError(f"codegraph sync falló:\n{out[-2000:]}")
        return "codegraph sync"
    return "codegraph status ok"


def ensure_repomix(origen: Path, dest: Path) -> str:
    rm = which("repomix")
    if not rm:
        raise RuntimeError("repomix no está instalado. Corre: uv run soporte doctor")
    dest.parent.mkdir(parents=True, exist_ok=True)
    code, out = run(
        [
            rm,
            native(origen),
            "-o",
            native(dest),
            "--style",
            "xml",
            "--compress",
            "--ignore",
            IGNORE,
        ],
        timeout=600,
    )
    if code != 0 or not dest.is_file():
        raise RuntimeError(f"repomix falló:\n{out[-2000:]}")
    return native(dest)


def add_project(origen_raw: str, nombre: str = "") -> dict:
    origen = Path(origen_raw.strip().strip('"')).expanduser()
    if not origen.is_dir():
        raise RuntimeError(f"no es una carpeta: {origen}")
    name = nombre.strip() or origen.name
    slug = slugify(name)
    pack = packs_dir() / slug / "repomix.xml"
    cg_note = ensure_codegraph(origen)
    pack_path = ensure_repomix(origen, pack)
    entry = {
        "id": slug,
        "nombre": name,
        "origen": native(origen),
        "pack": pack_path,
    }
    catalog = load_catalog()
    existing = [p for p in catalog["proyectos"] if p.get("id") != slug and p.get("origen") != entry["origen"]]
    existing.append(entry)
    catalog["proyectos"] = existing
    save_catalog(catalog)
    entry["_note"] = f"{cg_note}; pack {pack_path}"
    return entry

"""Mapa Archify por proyecto: evidencia CodeGraph + pack, sin inventar topología."""
from __future__ import annotations

import json
import re
from pathlib import Path

from soporte_sipecom.detect import archify_root, which, which_node
from soporte_sipecom.ingest import native, run, slugify

SKIP = {
    "bin",
    "obj",
    "packages",
    "node_modules",
    ".git",
    ".vs",
    ".codegraph",
    "dist",
    "__pycache__",
    "precompiledweb",
    "logs",
}

TYPE_HINTS = (
    (("segur", "auth", "login", "llave"), "security"),
    (("sql", "bd", "data", "db"), "database"),
    (("web", "mvc", "ui", "front", "aspx", "portal"), "frontend"),
)


def maps_dir(slug: str) -> Path:
    path = Path.home() / ".soporte-sipecom" / "maps" / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def _slug_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return (slug or "nodo")[:40]


def _kind(name: str) -> str:
    low = name.lower()
    for keys, kind in TYPE_HINTS:
        if any(k in low for k in keys):
            return kind
    return "backend"


def _top_folders(origen: Path) -> list[str]:
    names: list[str] = []
    cg = which("codegraph")
    if cg:
        code, out = run([cg, "files", "--path", native(origen), "--format", "tree", "--max-depth", "2"], timeout=60)
        if code == 0:
            for line in out.splitlines():
                raw = line.replace("│", " ").replace("├", " ").replace("└", " ").replace("─", " ").strip()
                if not raw or raw.startswith("codegraph"):
                    continue
                name = Path(raw.split()[0]).name
                if name and name.lower() not in SKIP and name not in names:
                    names.append(name)
                if len(names) >= 10:
                    break
    if names:
        return names[:10]
    try:
        for child in sorted(origen.iterdir(), key=lambda p: p.name.lower()):
            if child.name.startswith("."):
                continue
            if child.name.lower() in SKIP:
                continue
            if child.is_dir():
                names.append(child.name)
            if len(names) >= 10:
                break
    except OSError:
        pass
    return names


def build_spec(proyecto: dict) -> dict:
    origen = Path(proyecto.get("origen") or ".")
    nombre = proyecto.get("nombre") or origen.name
    folders = _top_folders(origen)[:9]
    if not folders:
        folders = [nombre]
    components = []
    used: set[str] = set()
    cols = 3
    cell_w, cell_h = 150, 64
    gap_x, gap_y = 52, 48
    ox, oy = 48, 48
    for i, folder in enumerate(folders):
        kind = _kind(folder)
        cid = _slug_id(folder) or f"n{i}"
        base = cid
        n = 2
        while cid in used:
            cid = f"{base}-{n}"
            n += 1
        used.add(cid)
        row, col = divmod(i, cols)
        x = ox + col * (cell_w + gap_x)
        y = oy + row * (cell_h + gap_y)
        components.append(
            {
                "id": cid,
                "type": kind,
                "label": folder[:28],
                "sublabel": kind,
                "pos": [x, y],
                "size": [cell_w, cell_h],
            }
        )
    connections = []
    for a, b in zip(components, components[1:]):
        connections.append({"id": f"{a['id']}-to-{b['id']}"[:48], "from": a["id"], "to": b["id"]})
    return {
        "schema_version": 1,
        "diagram_type": "architecture",
        "meta": {
            "title": str(nombre)[:80],
            "subtitle": "CodeGraph + pack",
            "quality_profile": "standard",
        },
        "components": components,
        "connections": connections[:8],
        "cards": [
            {
                "dot": "cyan",
                "title": "Evidencia",
                "items": [
                    "Carpetas del origen vía CodeGraph",
                    "Pack Repomix para el detalle en el chat",
                ],
            }
        ],
    }


def pretty_archify_error(out: str) -> str:
    messages = re.findall(r'"message"\s*:\s*"((?:\\.|[^"\\])*)"', out)
    if messages:
        lines = []
        for raw in messages[:3]:
            text = raw.replace("\\n", " ").replace('\\"', '"')
            lines.append(text[:160])
        return "Archify: el layout chocaba. Ya se reubican los nodos. " + " · ".join(lines)
    compact = " ".join(out.split())
    return compact[-500:] or "archify deliver falló"


def existing_artifacts(proyecto: dict) -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()

    def add(path: Path) -> None:
        key = str(path.resolve()) if path.exists() else ""
        if not key or key in seen:
            return
        if path.suffix.lower() in {".html", ".png", ".webp"}:
            seen.add(key)
            found.append(path)

    for key in ("mapa_html", "mapa"):
        raw = proyecto.get(key) or ""
        if raw:
            add(Path(raw))
    mapas = proyecto.get("mapas") or ""
    if mapas:
        root = Path(mapas)
        if root.is_dir():
            for path in sorted(root.glob("*")):
                add(path)
    slug = proyecto.get("id") or slugify(proyecto.get("nombre") or "proyecto")
    gen = maps_dir(slug)
    for path in sorted(gen.glob("*")):
        add(path)
    return found


def render_mapa(proyecto: dict) -> dict:
    node = which_node()
    root = archify_root()
    if not node or not root:
        raise RuntimeError("Archify necesita Node y bin/archify.mjs")
    slug = proyecto.get("id") or slugify(proyecto.get("nombre") or "proyecto")
    dest = maps_dir(slug)
    spec_path = dest / "architecture.json"
    html_path = dest / "architecture.html"
    spec = build_spec(proyecto)
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    script = root / "bin" / "archify.mjs"
    code, out = run(
        [node, native(script), "deliver", "architecture", native(spec_path), native(html_path), "--quality", "standard", "--json"],
        timeout=120,
    )
    if code != 0 or not html_path.is_file():
        raise RuntimeError(pretty_archify_error(out))
    png = dest / "architecture.png"
    run([node, native(script), "visual-check", native(html_path), "--json"], timeout=90)
    for candidate in dest.glob("*.png"):
        png = candidate
        break
    return {"html": native(html_path), "png": native(png) if png.is_file() else "", "spec": native(spec_path)}

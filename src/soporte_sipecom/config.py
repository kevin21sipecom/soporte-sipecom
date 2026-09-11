"""Config local: agentes elegidos y puerto 2121."""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_PORT = 2121


def config_path() -> Path:
    return Path.home() / ".soporte-sipecom.json"


def load() -> dict:
    path = config_path()
    if not path.is_file():
        return {"port": DEFAULT_PORT, "agents": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"port": DEFAULT_PORT, "agents": []}
    data.setdefault("port", DEFAULT_PORT)
    data.setdefault("agents", [])
    return data


def save(data: dict) -> Path:
    path = config_path()
    payload = {
        "port": int(data.get("port") or DEFAULT_PORT),
        "agents": list(data.get("agents") or []),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path

"""Hilos de chat persistentes (estilo lista Hermes)."""
from __future__ import annotations

import json
import time
from pathlib import Path


def chats_root() -> Path:
    path = Path.home() / ".soporte-sipecom" / "chats"
    path.mkdir(parents=True, exist_ok=True)
    return path


def index_path() -> Path:
    return chats_root() / "index.json"


def load_index() -> list[dict]:
    path = index_path()
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    items = data if isinstance(data, list) else []
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("id") or "")
        if not cid or cid in seen:
            continue
        seen.add(cid)
        unique.append(item)
    return unique


def save_index(items: list[dict]) -> None:
    index_path().write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def thread_dir(cid: str) -> Path:
    path = chats_root() / cid
    path.mkdir(parents=True, exist_ok=True)
    return path


def title_from_messages(messages: list[dict]) -> str:
    for item in messages:
        if item.get("role") == "user" and (item.get("content") or "").strip():
            return " ".join(item["content"].split())[:72]
    return "Nueva conversación"


def load_thread(cid: str) -> tuple[list[dict], list[str]]:
    path = thread_dir(cid) / "thread.json"
    if not path.is_file():
        return [], []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], []
    return list(data.get("messages") or []), list(data.get("images") or [])


def save_thread(cid: str, messages: list[dict], images: list[str], project: str = "") -> None:
    path = thread_dir(cid) / "thread.json"
    payload = {"messages": messages, "images": images, "project": project}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    title = title_from_messages(messages)
    items = [x for x in load_index() if x.get("id") != cid]
    items.insert(
        0,
        {"id": cid, "title": title, "project": project, "updated": time.time()},
    )
    save_index(items[:40])


def new_id() -> str:
    return str(int(time.time() * 1000))

"""Modelos e effort: salen de la CLI seleccionada, no de una lista fija."""
from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from soporte_sipecom.constants import VALID_AGENTS
from soporte_sipecom.detect import run_cmd, which

CACHE_TTL_S = 600
GROK_EFFORTS = ["low", "medium", "high", "xhigh"]
AGY_EFFORTS = ["low", "medium", "high"]
BAKED_EFFORTS = ("medium", "high", "low")


def baked_effort(model_id: str) -> str | None:
    """Si el id ya trae el effort (gemini-3.8-flash-high), no se puede pasar --effort."""
    low = (model_id or "").strip().lower()
    for level in BAKED_EFFORTS:
        if low.endswith(f"-{level}") or low.endswith(f"_{level}"):
            return level
    return None


@dataclass
class ModelInfo:
    id: str
    label: str = ""
    default: bool = False
    efforts: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def cache_path() -> Path:
    path = Path.home() / ".soporte-sipecom"
    path.mkdir(parents=True, exist_ok=True)
    return path / "models-cache.json"


def _load_cache() -> dict:
    path = cache_path()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(data: dict) -> None:
    try:
        cache_path().write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        return


def parse_grok_models(text: str) -> list[ModelInfo]:
    models: list[ModelInfo] = []
    seen: set[str] = set()
    default_id = ""
    for raw in text.splitlines():
        line = raw.strip()
        lower = line.lower()
        if lower.startswith("default model:"):
            default_id = line.split(":", 1)[1].strip()
            continue
        if not (line.startswith("*") or line.startswith("-")):
            continue
        token = re.split(r"\s+", line.lstrip("*- ").strip())
        if not token:
            continue
        mid = token[0].strip("(),")
        if not mid or mid.lower() in {"available", "models:"}:
            continue
        if mid in seen:
            continue
        seen.add(mid)
        is_default = "*" in line[:3] or "(default)" in lower or mid == default_id
        models.append(ModelInfo(id=mid, label=mid, default=is_default, efforts=list(GROK_EFFORTS)))
    if default_id and models and not any(m.default for m in models):
        for item in models:
            if item.id == default_id:
                item.default = True
                break
    if models and not any(m.default for m in models):
        models[0].default = True
    return models


def parse_agy_models(text: str) -> list[ModelInfo]:
    models: list[ModelInfo] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.lower().startswith("fetching"):
            continue
        if "\t" in line:
            mid, label = line.split("\t", 1)
        else:
            parts = re.split(r"\s{2,}", line, maxsplit=1)
            mid = parts[0]
            label = parts[1] if len(parts) > 1 else mid
        mid = mid.strip()
        label = label.strip() or mid
        if not mid or mid.startswith("-") or " " in mid and not mid[0].isalnum():
            continue
        if any(ch in mid for ch in " /\\"):
            continue
        if mid.lower() in {"id", "model", "models"}:
            continue
        if mid in seen:
            continue
        seen.add(mid)
        baked = baked_effort(mid)
        models.append(
            ModelInfo(
                id=mid,
                label=label,
                default=not models,
                efforts=[] if baked else list(AGY_EFFORTS),
            )
        )
    return models


def parse_codex_models(text: str) -> list[ModelInfo]:
    blob = text[text.find("{") : text.rfind("}") + 1] if "{" in text else ""
    if not blob:
        return []
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return []
    rows = data.get("models") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return []
    models: list[ModelInfo] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("visibility") or "list").lower() == "hide":
            continue
        slug = str(row.get("slug") or "").strip()
        if not slug:
            continue
        label = str(row.get("display_name") or slug).strip()
        efforts: list[str] = []
        for item in row.get("supported_reasoning_levels") or []:
            if isinstance(item, dict) and item.get("effort"):
                efforts.append(str(item["effort"]))
            elif isinstance(item, str):
                efforts.append(item)
        models.append(ModelInfo(id=slug, label=label, default=not models, efforts=efforts))
    return models


def _fetch_models(agent: str) -> list[ModelInfo]:
    path = which(agent)
    if not path:
        return []
    if agent == "grok":
        code, out = run_cmd([path, "models"], timeout=20)
        if code not in (0, None):
            return []
        return parse_grok_models(out)
    if agent == "antigravity":
        code, out = run_cmd([path, "models"], timeout=45)
        if code not in (0, None):
            return []
        return parse_agy_models(out)
    if agent == "codex":
        code, out = run_cmd([path, "debug", "models"], timeout=60)
        if code not in (0, None):
            return []
        return parse_codex_models(out)
    return []


def list_models(agent: str, *, refresh: bool = False) -> list[ModelInfo]:
    agent = (agent or "").strip().lower()
    if agent not in VALID_AGENTS:
        return []
    cache = _load_cache()
    entry = cache.get(agent) or {}
    now = time.time()
    if not refresh and entry.get("ts") and now - float(entry["ts"]) < CACHE_TTL_S:
        rows = entry.get("models") or []
        return [ModelInfo(**row) for row in rows if row.get("id")]
    models = _fetch_models(agent)
    cache[agent] = {"ts": now, "models": [m.as_dict() for m in models]}
    _save_cache(cache)
    return models


def list_efforts(agent: str, model_id: str = "", models: list[ModelInfo] | None = None) -> list[str]:
    agent = (agent or "").strip().lower()
    if agent == "antigravity" and baked_effort(model_id):
        return []
    infos = models if models is not None else list_models(agent)
    for item in infos:
        if item.id == model_id and item.efforts is not None:
            return list(item.efforts)
    if agent == "antigravity":
        return list(AGY_EFFORTS)
    if agent == "grok":
        return list(GROK_EFFORTS)
    if agent == "codex":
        return ["low", "medium", "high", "xhigh"]
    return ["medium"]


def default_model_id(models: list[ModelInfo]) -> str:
    for item in models:
        if item.default:
            return item.id
    return models[0].id if models else ""


def clamp_effort(agent: str, effort: str, allowed: list[str]) -> str:
    if effort in allowed:
        return effort
    if agent == "antigravity" and effort in {"xhigh", "max", "ultra"}:
        return "high" if "high" in allowed else (allowed[-1] if allowed else "high")
    return allowed[0] if allowed else effort

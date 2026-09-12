"""Estimación de tokens del hilo. CLI local no factura API."""
from __future__ import annotations


def estimate_tokens(text: str) -> int:
    raw = text or ""
    if not raw.strip():
        return 0
    return max(1, (len(raw) + 3) // 4)


def message_usage(item: dict) -> tuple[int, int]:
    tin = int(item.get("tokens_in") or 0)
    tout = int(item.get("tokens_out") or 0)
    if tin or tout:
        return tin, tout
    n = estimate_tokens(item.get("content") or "")
    if (item.get("role") or "") == "assistant":
        return 0, n
    return n, 0


def thread_usage(messages: list[dict]) -> tuple[int, int, int]:
    tin = tout = 0
    for item in messages or []:
        a, b = message_usage(item)
        tin += a
        tout += b
    return tin, tout, tin + tout


def format_int(n: int) -> str:
    return f"{int(n):,}".replace(",", ".")

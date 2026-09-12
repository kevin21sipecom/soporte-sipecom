"""Instala CodeGraph, Repomix y Archify desde el onboarding (s/n)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from soporte_sipecom.config import load, save
from soporte_sipecom.detect import WIN, _localappdata, archify_root, which

AUTO_TOOLS = ("codegraph", "repomix", "archify")
NPM_PACKAGES = {
    "codegraph": "@colbymchenry/codegraph",
    "repomix": "repomix",
}


def parse_answer(raw: str) -> bool | None:
    text = (raw or "").strip().lower()
    if text in {"s", "si", "sí", "y", "yes"}:
        return True
    if text in {"n", "no"}:
        return False
    return None


def ask_yes_no(question: str) -> bool | None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return None
    while True:
        try:
            answer = parse_answer(input(f"{question} [s/n]: "))
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        if answer is not None:
            return answer
        print("Responde s o n.")


def product_archify_dir() -> Path:
    return _localappdata() / "sipecom-soporte" / "archify"


def bundled_archify() -> Path | None:
    path = Path(__file__).resolve().parent / "vendor" / "archify"
    if (path / "bin" / "archify.mjs").is_file():
        return path
    return None


def archify_source() -> Path | None:
    dest = product_archify_dir()
    if (dest / "bin" / "archify.mjs").is_file():
        return dest
    bundled = bundled_archify()
    if bundled:
        return bundled
    root = archify_root()
    if root and (root / "bin" / "archify.mjs").is_file():
        return root
    hermes = _localappdata() / "hermes" / "skills" / "creative" / "archify"
    if (hermes / "bin" / "archify.mjs").is_file():
        return hermes
    return None


def _refresh_npm_path() -> None:
    npm_dir = Path(os.environ.get("APPDATA") or "") / "npm"
    if npm_dir.is_dir():
        os.environ["PATH"] = str(npm_dir) + os.pathsep + os.environ.get("PATH", "")


def _run_live(argv: list[str], timeout: int = 300) -> int:
    print(f"  → {' '.join(argv)}")
    try:
        completed = subprocess.run(argv, timeout=timeout)
        return int(completed.returncode)
    except FileNotFoundError:
        print("  no se encontró el comando")
        return 1
    except subprocess.TimeoutExpired:
        print("  tardó demasiado")
        return 1


def _persist_archify_home(dest: Path) -> None:
    os.environ["ARCHIFY_HOME"] = str(dest)
    cfg = load()
    cfg["archify_home"] = str(dest)
    save(cfg)
    if WIN:
        subprocess.run(
            ["setx", "ARCHIFY_HOME", str(dest)],
            capture_output=True,
            text=True,
            timeout=30,
        )


def install_npm_tool(name: str) -> tuple[bool, str]:
    package = NPM_PACKAGES[name]
    npm = which("npm")
    if not npm:
        return False, "npm no está"
    code = _run_live([npm, "i", "-g", package, "--no-fund", "--no-audit"])
    _refresh_npm_path()
    if code != 0:
        return False, f"npm i -g {package} falló (exit {code})"
    return True, package


def install_archify() -> tuple[bool, str]:
    dest = product_archify_dir()
    src = archify_source()
    if src is None:
        return False, "no hay Archify en el paquete ni en esta PC"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() != dest.resolve():
        shutil.copytree(
            src,
            dest,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("examples", "test", "node_modules", ".git"),
        )
    if not (dest / "bin" / "archify.mjs").is_file():
        return False, "copia incompleta de Archify"
    _persist_archify_home(dest)
    return True, str(dest)


def install_missing(names: list[str]) -> dict[str, tuple[bool, str]]:
    results: dict[str, tuple[bool, str]] = {}
    for name in names:
        print(f"\nInstalando {name}…")
        if name in NPM_PACKAGES:
            results[name] = install_npm_tool(name)
        elif name == "archify":
            results[name] = install_archify()
        else:
            results[name] = (False, "no hay instalador automático")
        ok, detail = results[name]
        print(f"  {'OK' if ok else 'NO'}  {detail}")
    return results

"""Banner típico de CLI."""
from __future__ import annotations

import pyfiglet

TITLE = "SIPECOM"
SUB = "SOPORTE"
PORT = 2121


def banner(port: int = PORT) -> str:
    top = pyfiglet.figlet_format(TITLE, font="slant", width=80).rstrip()
    bottom = pyfiglet.figlet_format(SUB, font="slant", width=80).rstrip()
    line = "-" * 64
    return (
        f"{top}\n{bottom}\n"
        f"{line}\n"
        f"  SIPECOM-SOPORTE  ·  puerto {port}  ·  uv run soporte\n"
        f"{line}"
    )

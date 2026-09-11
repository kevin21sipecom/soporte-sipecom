# SIPECOM-SOPORTE

CLI de soporte en Python, instalable con `uv`.

Puerto por defecto: **2121**.

## Qué hace primero

1. Banner `SIPECOM-SOPORTE` (figlet `slant`).
2. Valida **4 familias** (sin API keys, sin TUI):
   - CodeGraph
   - Repomix
   - Archify (`node bin/archify.mjs` — CLI de la skill, no hace falta Hermes)
   - Agentes headless: Codex / Grok / Claude (al menos uno)
3. Permite **seleccionar** qué agentes usar.

```text
uv sync
uv run sipecom-soporte
uv run sipecom-soporte doctor
uv run sipecom-soporte select --use grok,codex
uv run sipecom-soporte dashboard
```

`sipecom-soporte dashboard` abre **esta** consola Streamlit (puerto **2121**): header, Sipi, sidebar de motor, chat. CLI local, sin API keys. `ui` es alias.

Config: `~/.soporte-sipecom.json`

## Consola

![Consola SIPECOM-SOPORTE](docs/consola-ui.png)

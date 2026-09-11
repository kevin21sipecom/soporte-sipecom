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
uv run soporte
uv run soporte doctor
uv run soporte select --use grok,codex
uv run soporte config
```

Config: `~/.soporte-sipecom.json`

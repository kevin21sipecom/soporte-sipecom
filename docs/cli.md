# CLI

Punto de entrada: `sipecom-soporte` (alias `soporte`).

```text
uv run sipecom-soporte --help
```

## doctor

Valida CodeGraph, Repomix, Archify y las CLIs de agente.

```text
uv run sipecom-soporte doctor
uv run sipecom-soporte doctor --json
```

## models

Pregunta a cada CLI qué modelos expone **ahora**. No usa una lista fija.

```text
uv run sipecom-soporte models
uv run sipecom-soporte models --refresh
uv run sipecom-soporte models --json
```

- **grok** → `grok models`
- **antigravity** → `agy models`
- **codex** → `codex debug models`

## select

Guarda qué agentes usará el dashboard.

```text
uv run sipecom-soporte select --use grok,antigravity,codex
```

`agy` se normaliza a `antigravity`. Cualquier otro nombre se rechaza.

## config

Muestra puerto y agentes en `~/.soporte-sipecom.json`.

```text
uv run sipecom-soporte config
uv run sipecom-soporte --port 2121 config
```

## dashboard

Arranca Streamlit **solo en localhost**.

```text
uv run sipecom-soporte dashboard
```

Escucha `127.0.0.1` (no `0.0.0.0`). No hay túnel. Alias: `ui`.

# Instalación

## Entorno

- Windows 10/11 (el desarrollo actual es Windows).
- Python ≥ 3.11.
- `uv` en PATH.

```text
uv sync
uv run sipecom-soporte doctor
```

El doctor cubre cuatro familias:

1. CodeGraph
2. Repomix
3. Archify (`node bin/archify.mjs`)
4. Agentes: grok, antigravity (`agy`) o codex — basta uno headless

Claude no forma parte de las CLIs válidas de este producto.

## Agentes

Instala y autentica cada CLI por su propio flujo (login local). SIPECOM-SOPORTE no guarda API keys para el modo CLI.

Rutas habituales de binario (el detector las busca si no están en PATH):

- Grok: `~/.grok/bin/grok`
- Codex: instalación estándar de OpenAI Codex
- Antigravity: `agy` (carpeta local `agy/bin`)

Comprueba modelos:

```text
uv run sipecom-soporte models
```

## Puerto

Por defecto **2121**, solo en `127.0.0.1`.

```text
uv run sipecom-soporte --port 2121 dashboard
```

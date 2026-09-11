# Instalación (toda la PC)

De momento solo **Windows**. No está validado en Linux ni macOS.

## Instalar uv

Windows (PowerShell):

```text
powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Cierra y abre la terminal. Comprueba:

```text
uv --version
```

Docs: https://docs.astral.sh/uv/getting-started/installation/

## Producto

```text
uv tool install git+https://github.com/kevin21sipecom/soporte-sipecom.git
uv tool update-shell
sipecom-soporte
sipecom-soporte dashboard
```

Python 3.11+ y [uv](https://docs.astral.sh/uv/). No hace falta quedarse dentro de una carpeta clonada.

## Onboarding

`sipecom-soporte` valida:

| Pieza | Si falta |
| --- | --- |
| Node.js / npm | `winget install OpenJS.NodeJS.LTS` y reabrir la terminal |
| Repomix | `npm install -g repomix` |
| CodeGraph | CLI en PATH |
| Archify | Node + `bin/archify.mjs` (skill o `ARCHIFY_HOME`) |
| grok / agy / codex | su propio instalador + login |

El dashboard elige qué agente usar. `select --use` es opcional.

## Puerto

**2121**, solo `127.0.0.1`.

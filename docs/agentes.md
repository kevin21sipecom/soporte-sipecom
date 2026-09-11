# Agentes

CLIs válidas de este producto: **grok**, **antigravity**, **codex**.

No se inventan flags. Cada invocación usa opciones que salen del `--help` de esa versión.

## Cómo se elige el modelo

1. El usuario selecciona la CLI en el dashboard (o con `select`).
2. SIPECOM-SOPORTE ejecuta el comando de listado de **esa** CLI.
3. Rellena el desplegable Modelo (y Effort si el catálogo lo trae).
4. La consulta se lanza con el id elegido.

| Nombre en UI | Binario | Listar modelos | Effort | Headless |
| --- | --- | --- | --- | --- |
| grok | `grok` | `grok models` | `--reasoning-effort` | `--prompt-file` |
| antigravity | `agy` | `agy models` | `--effort` `low\|medium\|high` | `--print` |
| codex | `codex` | `codex debug models` | `-c model_reasoning_effort=` | `codex exec` |

## grok

```text
grok --prompt-file <prompt.md> -m <modelo> --reasoning-effort <effort> --output-format plain --permission-mode bypassPermissions --disable-web-search --cwd <origen>
```

No combinar `-p` vacío con `--prompt-file`.

## antigravity

Binario: `agy`. En la UI el nombre es `antigravity`.

```text
agy --model <modelo> --effort <low|medium|high> --dangerously-skip-permissions --disable-slash-commands --output-format text --add-dir <origen> --print-timeout <Ns> --print <prompt>
```

En Gemini el effort va **en el id** (`gemini-3.8-flash-high`). No se pasa `--effort` a la vez: la CLI responde `conflicts with --effort`. En Claude/otros sin sufijo sí se usa `--effort`.

## codex

```text
codex exec --skip-git-repo-check -m <modelo> -c model_reasoning_effort=<effort> --sandbox danger-full-access <prompt>
```

Los orígenes pueden no ser git: hace falta `--skip-git-repo-check`. El catálogo de modelos se lee con `codex debug models` (JSON). Solo se muestran entradas con visibilidad distinta de `hide`.

## Auth

Cada CLI usa su sesión local. El modo «CLI local» no envía API keys. El modo «API key» de la UI aún no ejecuta remoto.

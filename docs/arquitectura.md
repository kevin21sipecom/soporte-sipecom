# Arquitectura

Paquete Python `soporte_sipecom`, instalable con `uv`.

```text
sipecom-soporte / soporte
        │
        ├─ doctor / select / models / config
        └─ dashboard  →  Streamlit 127.0.0.1:2121
                              │
                              ├─ ingest   CodeGraph + Repomix
                              ├─ models   listado vivo por CLI
                              └─ engine   grok | agy | codex exec
```

## Módulos

| Módulo | Responsabilidad |
| --- | --- |
| `cli.py` | Argumentos, doctor, dashboard localhost |
| `detect.py` | Binarios, aliases (`antigravity` → `agy`) |
| `models.py` | Parseo de `grok models`, `agy models`, `codex debug models` |
| `engine.py` | Lanzar la CLI elegida, sin API keys |
| `ingest.py` | Registrar proyecto: grafo + pack |
| `config.py` | `~/.soporte-sipecom.json` |
| `ui/app.py` | Consola Streamlit |

## Principios

- CLIs válidas: grok, antigravity, codex.
- Modelos: siempre desde el binario seleccionado.
- Dashboard: solo localhost, sin túnel.
- El pack Repomix se pasa por ruta; no se vuelca al prompt.
- Windows: rutas nativas `C:/...` hacia los exe.

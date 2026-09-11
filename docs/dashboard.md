# Dashboard

Consola Streamlit de SIPECOM-SOPORTE.

## Acceso

```text
uv run sipecom-soporte dashboard
```

URL: **http://127.0.0.1:2121**

- Bind: `127.0.0.1` (loopback).
- Sin Cloudflare ni ningún túnel.
- Headless: no abre un servicio en la red local.

## Layout

- **Sidebar:** proyecto, modo CLI local / API key, motor, modelo, effort, Sipi.
- **Principal:** chat nativo (`st.chat_input`).

Los modelos del desplegable salen de la CLI seleccionada (`grok models`, `agy models` o `codex debug models`). Si el listado falla, se puede escribir el id en «Modelo extra».

## Proyectos

«Agregar proyecto» indexa con **CodeGraph** y empaqueta con **Repomix** desde Python. El chat responde con pack + grafo + origen; no pega el XML al prompt.

## Captura

![Consola](consola-ui.png)

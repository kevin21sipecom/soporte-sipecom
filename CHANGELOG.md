# Changelog

## 0.6.2

- Borrar este hilo o empezar de cero (borra conversaciones en disco).

## 0.6.1

- OpenCode: `--file=` y `--` para que el mensaje no se tome como ruta.

## 0.6.0

- CLI **opencode**: `opencode run` headless; el desplegable solo lista modelos gratis (coste 0).

## 0.5.7

- El error y la captura van en el chat, no en el lateral.

## 0.5.6

- Tokens del hilo (estimado) y caja «Error de la app» (log/stack) distinta del chat.

## 0.5.5

- Archify va en el paquete: el onboarding ya no depende de la skill de Hermes.

## 0.5.4

- Índice de conversaciones centrado en vertical.
- Publicación a PyPI (Trusted Publishing) en cada GitHub Release.

## 0.5.3

- Ticks del índice: 2px de ancho (el CSS ahora pega al `button` de Streamlit).

## 0.5.2

- Índice a la derecha: un solo rail, ticks más finos, sin duplicar.

## 0.5.1

- Índice de conversaciones a la derecha, ticks muy chicos.

## 0.5.0

- Onboarding pregunta s/n e instala CodeGraph, Repomix y Archify sin salir.

## 0.4.1

- Doctor imprime comandos de instalación de CodeGraph y Archify.

## 0.4.0

- Paquete y comando: `sipecom-soporte` (`uv tool upgrade sipecom-soporte`).
- Conversaciones en una barrita lateral (estilo Hermes).

## 0.3.0

- Instalación global con `uv tool install` (no hace falta `cd` al repo).
- Onboarding: node/npm, CodeGraph, Repomix, Archify y agentes.
- El dashboard elige las CLIs (el detector las rellena). `select` es opcional.
- Imágenes del chat viven en la conversación y se recuerdan en el hilo.

## 0.2.0

- CLIs válidas: grok, antigravity (`agy`), codex.
- Modelos y effort se leen de cada CLI (`grok models`, `agy models`, `codex debug models`).
- Comando `sipecom-soporte models`.
- Dashboard solo en `127.0.0.1` (sin túnel).
- Documentación de producto en `docs/`.

## 0.1.0

- CLI inicial, doctor 4/4 y consola Streamlit en el puerto 2121.

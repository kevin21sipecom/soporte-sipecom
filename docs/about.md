# About · SIPECOM-SOPORTE

**SIPECOM-SOPORTE** es el producto de SIPECOM para consultar proyectos de software en local, con las CLIs de agente que ya están en la PC.

No es un chatbot en la nube. El código no sale por un túnel: la consola escucha solo en `http://127.0.0.1:2121`.

## Qué resuelve

Un equipo de soporte o modernización necesita preguntar por un origen (legado o actual) sin pegar el repositorio entero al modelo y sin inventar topología.

El producto:

1. Indexa el proyecto con **CodeGraph**.
2. Empaqueta el origen con **Repomix** (el pack se pasa por ruta; no se vuelca al prompt).
3. Deja un **mapa Archify** cuando hay evidencia para dibujarlo.
4. Pregunta con **grok**, **antigravity** (`agy`), **codex** u **opencode** (este último, solo modelos gratis).
5. Recuerda imágenes y el hilo por conversación. «Nueva conversación» empieza otro hilo.

Sipi es el asistente de la consola.

## Qué no es

- No es el chef de desposte ni un túnel Cloudflare.
- No pide API keys: usa el login local de cada CLI.
- No sustituye a QA ni a producción. Es herramienta de desarrollo / soporte en el puesto de trabajo.
- Linux y macOS no están validados. De momento, **solo Windows**.

## Distribución

- Paquete y comando: `sipecom-soporte`
- PyPI: https://pypi.org/project/sipecom-soporte/
- Código: https://github.com/kevin21sipecom/soporte-sipecom
- Release actual: [v0.5.4](https://github.com/kevin21sipecom/soporte-sipecom/releases/tag/v0.5.4)

```text
uv tool install sipecom-soporte
sipecom-soporte
sipecom-soporte dashboard
```

## Titular

SIPECOM. Licencia: [LICENSE](../LICENSE) (MIT, titular SIPECOM). El nombre, el logo y Sipi no se sublicencian.

Contacto del paquete: kfernandez@sipecom.com

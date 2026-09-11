# SIPECOM-SOPORTE

CLI global y consola local para consultar proyectos (CodeGraph + Repomix) con **grok**, **antigravity** o **codex**.

La UI es **localhost** (`127.0.0.1:2121`). Sin túnel.

**Plataforma:** de momento solo **Windows**. No está validado en Linux ni macOS.

![Consola SIPECOM-SOPORTE](docs/consola-ui.png)

## Instalar uv

Windows (PowerShell):

```text
powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Cierra y abre la terminal, luego `uv --version`.

## Instalar en toda la PC

No hace falta `cd` al repo. Desde PyPI:

```text
uv tool install sipecom-soporte
uv tool update-shell
sipecom-soporte
sipecom-soporte dashboard
```

Desde git (misma versión, sin PyPI):

```text
uv tool install git+https://github.com/kevin21sipecom/soporte-sipecom.git
```

Actualizar:

```text
uv tool upgrade sipecom-soporte
```

Desarrollo local (opcional): `git clone` + `uv sync` + `uv run sipecom-soporte`.

## Onboarding

`sipecom-soporte` (sin argumentos) comprueba:

1. **node** y **npm** (Repomix y Archify los necesitan)
2. **CodeGraph**, **Repomix**, **Archify**
3. Agentes: grok / antigravity (`agy`) / codex

Si falta CodeGraph, Repomix o Archify, pregunta s/n y los instala en el mismo onboarding. Cuando todo está OK:

```text
sipecom-soporte dashboard
```

Las CLIs las elige el **dashboard**. No hace falta `select --use`.

## Dashboard

- Motor = detector de CLIs de esta PC.
- Modelos = listado vivo de esa CLI.
- Proyecto: CodeGraph + pack Repomix (el pack no se vuelca al prompt).
- Imágenes: viven en **esta conversación**; puedes subir otra y se recuerdan las anteriores. «Nueva conversación» limpia el hilo.

## Comandos

| Comando | Descripción |
| --- | --- |
| `sipecom-soporte` | Onboarding |
| `sipecom-soporte doctor` | Mismas 4 familias, formato corto |
| `sipecom-soporte models` | Modelos de cada CLI |
| `sipecom-soporte dashboard` | Consola en localhost:2121 |
| `sipecom-soporte ui` | Alias de dashboard |

## Documentación

[docs/README.md](docs/README.md)

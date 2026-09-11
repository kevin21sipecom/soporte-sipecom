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

Actualizar:

```text
uv tool upgrade sipecom-soporte
```

Si tenías el paquete viejo `soporte-sipecom`:

```text
uv tool uninstall soporte-sipecom
uv tool install git+https://github.com/kevin21sipecom/soporte-sipecom.git
```

## Onboarding

`sipecom-soporte` valida las piezas y, si faltan, imprime el comando para instalarlas.

Usa **PowerShell normal** (no Administrador). Luego cierra y abre la terminal.

### CodeGraph

```text
npm i -g @colbymchenry/codegraph
```

Comprueba: `codegraph --version`

### Archify

No es un paquete npm. Es el CLI `bin/archify.mjs`. Con Hermes ya está en esa carpeta:

```text
setx ARCHIFY_HOME "%LOCALAPPDATA%\hermes\skills\creative\archify"
```

Si no tienes Hermes, copia una carpeta que tenga `bin\archify.mjs` y apunta `ARCHIFY_HOME` a esa carpeta.

Comprueba:

```text
node "%ARCHIFY_HOME%\bin\archify.mjs" doctor
```

### Repomix y Node

```text
winget install OpenJS.NodeJS.LTS
npm install -g repomix
```

### Agentes

grok / agy / codex: su propio instalador + login. El dashboard elige cuál usar. `select --use` es opcional.

## Puerto

**2121**, solo `127.0.0.1`.

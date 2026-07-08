# MCP Python Examples

Este proyecto tiene tres paquetes de servidor/cliente MCP en Python:

- [basico/mini_mcp.py](basico/mini_mcp.py): ejemplo mínimo para entender la estructura
- [basico/main.py](basico/main.py): ejemplo de clima usando Open-Meteo, sin seguridad
- [seguro/](seguro/) y [github_login/](github_login/): la misma tool de clima, pero
  protegida con OAuth 2.1 (Scalekit) — client credentials (M2M) y login real de
  usuario con GitHub

También incluye [index.html](index.html), una presentación explicando **uv**, **pipx** y **MCP** con `weather-mcp` como ejemplo real (arquitectura, seguridad, y cómo exponerlo en la nube). Ábrelo directo en el navegador.

## Qué se versiona en este repo

Solo el código y los archivos de configuración de uv, sin artefactos generados:

| Se versiona | No se versiona (ver [.gitignore](.gitignore)) |
| --- | --- |
| `basico/`, `seguro/`, `github_login/` (código) | `.venv/`, `__pycache__/` |
| `pyproject.toml`, `.python-version` | `*.egg-info`, `build/`, `dist/` |
| `index.html`, `README.md`, `.gitignore`, `.env.template` | `.uv-cache/`, `.claude/`, `.DS_Store`, `.env`, `usuarios_registrados.json` |

## Ejemplo mínimo

El archivo [basico/mini_mcp.py](basico/mini_mcp.py) es el más simple del proyecto.

Hace solo esto:
- crea un servidor MCP
- registra una sola tool
- devuelve un saludo

La tool se llama `saludar` y recibe:

```json
{
  "nombre": "Juan Camilo"
}
```

Respuesta esperada:

```json
{
  "result": "Hola, Juan Camilo"
}
```

## Cómo correrlo

Puedes correr el MCP mínimo de cualquiera de estas dos formas:

```bash
uv run python basico/mini_mcp.py
```

o:

```bash
uv run mini-mcp
```

No recibe argumentos por consola. Los parámetros se envían cuando un cliente MCP invoca la tool `saludar`.

## Cómo probarlo localmente

Modo desarrollo con inspector MCP:

```bash
uv run mcp dev basico/mini_mcp.py
```

Prueba directa como función Python:

```bash
uv run python -c "from basico.mini_mcp import saludar; print(saludar('Juan Camilo'))"
```

## Configurar en clientes MCP

La opción más estable en este proyecto es registrar este comando:

```bash
/Users/sebastianzapata/.local/bin/uv run --project /Users/sebastianzapata/mcp mini-mcp
```

Después de editar la configuración de cualquier cliente, reinicia la aplicación.

### Codex

Archivo:

`~/.codex/config.toml`

Bloque:

```toml
[mcp_servers.mini-mcp]
command = "/Users/sebastianzapata/.local/bin/uv"
args = ["run", "--project", "/Users/sebastianzapata/mcp", "mini-mcp"]
```

También puedes agregarlo con CLI:

```bash
codex mcp add mini-mcp -- /Users/sebastianzapata/.local/bin/uv run --project /Users/sebastianzapata/mcp mini-mcp
```

### Claude Desktop

Archivo:

`~/Library/Application Support/Claude/claude_desktop_config.json`

Dentro de `mcpServers`:

```json
{
  "mini-mcp": {
    "command": "/Users/sebastianzapata/.local/bin/uv",
    "args": [
      "run",
      "--frozen",
      "--with",
      "mcp[cli]",
      "--with-editable",
      "/Users/sebastianzapata/mcp",
      "mcp",
      "run",
      "/Users/sebastianzapata/mcp/basico/mini_mcp.py"
    ]
  }
}
```

También puedes instalarlo con:

```bash
uv run mcp install /Users/sebastianzapata/mcp/basico/mini_mcp.py --name mini-mcp --with-editable /Users/sebastianzapata/mcp
```

Para ensayarlo en Claude, abre un chat nuevo y pide:

```text
Usa la herramienta saludar del MCP mini-mcp con {"nombre":"Juan Camilo"}
```

### Antigravity

Archivo:

`~/Library/Application Support/Antigravity/User/settings.json`

Dentro de `mcpServers`:

```json
{
  "mini-mcp": {
    "command": "/Users/sebastianzapata/.local/bin/uv",
    "args": [
      "run",
      "--project",
      "/Users/sebastianzapata/mcp",
      "mini-mcp"
    ]
  }
}
```

## Ejemplo de clima

El archivo [basico/main.py](basico/main.py) es un ejemplo más completo.

Expone la tool `get_weather`, recibe:

```json
{
  "latitude": 4.711,
  "longitude": -74.0721,
  "elevation": 2640
}
```

Consulta la API de Open-Meteo y devuelve el clima actual.

Ejecutarlo:

```bash
uv run python basico/main.py
```

o:

```bash
uv run weather-mcp
```

Modo desarrollo:

```bash
uv run mcp dev basico/main.py
```

Notas:
- usa Open-Meteo: https://open-meteo.com/en/docs
- `elevation` es opcional

### Registrado en Claude Code

```bash
claude mcp add weather-mcp -- /Users/sebastianzapata/.local/bin/uv run --project /Users/sebastianzapata/mcp weather-mcp
```

### Registrado en Codex

En `~/.codex/config.toml`:

```toml
[mcp_servers.weather-mcp]
command = "/Users/sebastianzapata/.local/bin/uv"
args = ["run", "--project", "/Users/sebastianzapata/mcp", "weather-mcp"]
```

## Login de usuario con GitHub (Scalekit)

`seguro/secure_mcp.py` valida tokens, pero hasta ahora solo los generaban
scripts (client credentials / M2M): ningún humano iniciaba sesión de verdad.
`github_login/app.py` añade ese flujo: una persona se autentica con su cuenta
de **GitHub** a través de Scalekit, queda registrada, y el token que recibe
sirve exactamente igual para llamar al MCP seguro.

Requisitos previos en el Dashboard de Scalekit:
- Tener habilitada una conexión social de **GitHub**.
- Registrar `http://localhost:8787/callback` (o el valor que uses en
  `SCALEKIT_REDIRECT_URI`) como Redirect URI permitido.

Ejecutarlo:

```bash
cp .env.template .env   # si no lo has hecho ya; agrega tus credenciales de Scalekit
uv run github-login
```

Luego:
1. Abre `http://localhost:8787` en el navegador.
2. Haz clic en "Iniciar sesión con GitHub".
3. Tras autorizar en GitHub, Scalekit te redirige de vuelta con un token de
   usuario y lo registra en `github_login/usuarios_registrados.json` (solo
   local, no se sube a git — ver `.gitignore`).
4. Usa ese token como cualquier otro Bearer token contra `secure-mcp`:

```bash
claude mcp add --transport http secure-mcp \
  https://tu-dominio.com/sse \
  --header "Authorization: Bearer <token_del_usuario>"
```

Los dos flujos conviven: `weather_client.py` e `inspector_cloud.py` siguen
usando client credentials (un Agente autenticándose a sí mismo), mientras que
`github_login/app.py` autentica a una persona real. `secure_mcp.py` no
distingue entre ambos: solo valida que el token sea un JWT vigente firmado
por tu entorno de Scalekit.

## Seguridad

`basico/main.py` ya sigue estas prácticas:

- **Sin API key**: Open-Meteo es pública, no hay secretos que proteger o filtrar.
- **Validación de entrada**: `latitude`/`longitude` se validan contra rangos físicos antes de armar la URL.
- **TLS verificado**: usa un `SSLContext` con el bundle de `certifi`, no desactiva la verificación de certificados.
- **Timeout explícito**: 15s, para que una API externa lenta no cuelgue el servidor.
- **Alcance mínimo**: una sola tool de solo lectura, sin acceso a filesystem ni shell.

Reglas generales para servidores MCP propios o de terceros:

- Secretos siempre en variables de entorno, nunca hardcodeados en el código.
- Si agregas un `.env` con claves, súmalo a `.gitignore` (ya cubre `.venv` y caches).
- Cada tool debe hacer una sola cosa bien definida; evita tools genéricas tipo "ejecutar comando" o "leer cualquier archivo".
- Revisa el código de cualquier servidor MCP de terceros antes de instalarlo — corre con tus permisos locales.
- Fija versiones de dependencias (considera generar un `uv.lock`).

## Publicarlo para que otros lo descarguen

**GitHub**: el repo ya existe en [github.com/sebastianzapatar/mcp2026](https://github.com/sebastianzapatar/mcp2026) (rama `main`). Para subir el resto de archivos:

```bash
git add basico/ seguro/ github_login/ pyproject.toml .python-version index.html README.md .gitignore .env.template
git commit -m "Add weather MCP server and presentation"
git push
```

**PyPI** (instalable con `pip install weather-mcp` o `uvx weather-mcp`, requiere cuenta en pypi.org y un token de API):

```bash
uv build
uv publish
```

**Directorios de MCP**: con el repo público en GitHub, puedes enviarlo al [registro comunitario de MCP](https://github.com/modelcontextprotocol/servers) o a directorios como Smithery/Glama.

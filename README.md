# MCP Python Examples

Este proyecto tiene dos ejemplos de servidor MCP en Python:

- [mini_mcp.py](/Users/sebastianzapata/mcp/mini_mcp.py:1): ejemplo mínimo para entender la estructura
- [main.py](/Users/sebastianzapata/mcp/main.py:1): ejemplo de clima usando Open-Meteo

## Ejemplo mínimo

El archivo [mini_mcp.py](/Users/sebastianzapata/mcp/mini_mcp.py:1) es el más simple del proyecto.

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
uv run python mini_mcp.py
```

o:

```bash
uv run mini-mcp
```

No recibe argumentos por consola. Los parámetros se envían cuando un cliente MCP invoca la tool `saludar`.

## Cómo probarlo localmente

Modo desarrollo con inspector MCP:

```bash
uv run mcp dev mini_mcp.py
```

Prueba directa como función Python:

```bash
uv run python -c "from mini_mcp import saludar; print(saludar('Juan Camilo'))"
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
      "/Users/sebastianzapata/mcp/mini_mcp.py"
    ]
  }
}
```

También puedes instalarlo con:

```bash
uv run mcp install /Users/sebastianzapata/mcp/mini_mcp.py --name mini-mcp --with-editable /Users/sebastianzapata/mcp
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

El archivo [main.py](/Users/sebastianzapata/mcp/main.py:1) es un ejemplo más completo.

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
uv run python main.py
```

o:

```bash
uv run weather-mcp
```

Modo desarrollo:

```bash
uv run mcp dev main.py
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

## Seguridad

`main.py` ya sigue estas prácticas:

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

No publicado todavía — son pasos manuales porque requieren tus propias cuentas y son acciones públicas difíciles de revertir.

**GitHub** (más simple, cualquiera clona y corre `uv run weather-mcp`):

```bash
git add main.py mini_mcp.py pyproject.toml README.md .gitignore
git commit -m "Add weather MCP server"
gh repo create weather-mcp --public --source=. --remote=origin
git push -u origin master
```

**PyPI** (instalable con `pip install weather-mcp` o `uvx weather-mcp`, requiere cuenta en pypi.org y un token de API):

```bash
uv build
uv publish
```

**Directorios de MCP**: con el repo público en GitHub, puedes enviarlo al [registro comunitario de MCP](https://github.com/modelcontextprotocol/servers) o a directorios como Smithery/Glama.

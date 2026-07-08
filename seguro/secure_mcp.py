"""
SERVIDOR MCP SEGURO CON OAUTH 2.1 (SCALEKIT)
--------------------------------------------
Este script expone el servidor MCP de CLIMA a Internet usando HTTP (SSE).
Protegido por Scalekit para que solo Agentes autorizados puedan ver el clima.

Acepta dos tipos de token, porque conviven dos flujos de autorización:
- Tokens de máquina (client credentials), generados por un Agente/script
  (ver weather_client.py e inspector_cloud.py).
- Tokens de un usuario humano autenticado con GitHub
  (ver github_login/app.py, que implementa el login real prometido en la
  diapositiva "OAuth 2.1 y Scalekit" de la presentación).
Este servidor no distingue entre ambos: solo valida que el token sea un JWT
vigente y firmado por tu entorno de Scalekit.
"""

import os
import json
import ssl
from typing import Any
from urllib.request import urlopen
from urllib.parse import urlencode

import certifi
import uvicorn
from fastapi import Request
from fastapi.responses import Response

# Componentes de MCP
from mcp.server.fastmcp import FastMCP

# Componentes de Scalekit para Auth
from scalekit import ScalekitClient
from dotenv import load_dotenv

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 15
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

CURRENT_VARIABLES = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"]

# Cargar variables desde el archivo .env
load_dotenv()

# 1. Configuración de Scalekit
# Normalmente estas variables de entorno se obtienen del Dashboard de Scalekit.
env_url = os.getenv("SCALEKIT_ENVIRONMENT_URL", "https://api.scalekit.com")
client_id = os.getenv("SCALEKIT_CLIENT_ID", "tu_client_id_aqui")
client_secret = os.getenv("SCALEKIT_CLIENT_SECRET", "tu_client_secret_aqui")

# Inicializamos el cliente de Scalekit
sc = ScalekitClient(env_url, client_id, client_secret)

# 2. Configurar el Servidor MCP (FastMCP)
mcp = FastMCP("secure-mcp")

def _fetch_weather(latitude: float, longitude: float) -> dict[str, Any]:
    params = {
        "latitude": latitude, "longitude": longitude,
        "current": ",".join(CURRENT_VARIABLES), "timezone": "auto",
    }
    url = f"{WEATHER_API_URL}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS, context=SSL_CONTEXT) as response:
            return json.load(response)
    except Exception as exc:
        raise RuntimeError(f"Error consultando el clima: {exc}")

@mcp.tool(name="get_weather")
def get_weather(latitude: float, longitude: float) -> dict[str, Any]:
    """
    Obtiene el clima actual.
    ESTA HERRAMIENTA ESTÁ PROTEGIDA POR OAUTH EN LA NUBE.
    """
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Coordenadas inválidas")
    return _fetch_weather(latitude=latitude, longitude=longitude)


# 3. Aplicación ASGI con Middleware de Autorización
# mcp.sse_app() ya es una app ASGI completa (no un router de FastAPI), así que
# no podemos protegerla con `Depends`. En su lugar envolvemos esa app en una
# función ASGI propia que revisa el header Authorization antes de delegarle
# la petición.
mcp_app = mcp.sse_app()

async def secure_app(scope, receive, send):
    if scope["type"] == "http":
        request = Request(scope, receive)
        # Solo protegemos los endpoints del protocolo MCP; el resto de rutas
        # (si las hubiera) pasan sin autenticación.
        if request.url.path in ["/sse", "/messages"]:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                response = Response(status_code=401, content="Falta el token Bearer")
                return await response(scope, receive, send)

            token = auth_header.split(" ")[1]
            try:
                # Válido tanto para tokens de máquina (client credentials)
                # como para tokens de usuario emitidos tras el login con
                # GitHub: ambos son JWT firmados por el mismo entorno Scalekit.
                is_valid = sc.validate_access_token(token)
                if not is_valid:
                    response = Response(status_code=401, content="El token es inválido")
                    return await response(scope, receive, send)
            except Exception as exc:
                response = Response(status_code=401, content=f"Autenticación fallida: {exc}")
                return await response(scope, receive, send)

    # Delegar la petición HTTP al servidor nativo de FastMCP
    await mcp_app(scope, receive, send)

def main() -> None:
    print("Iniciando servidor MCP seguro con OAuth 2.1 (Scalekit) en el puerto 8000...")
    print("Las peticiones a /sse y /messages ahora requieren un header:")
    print("Authorization: Bearer <tu_token_aqui>")
    uvicorn.run(secure_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

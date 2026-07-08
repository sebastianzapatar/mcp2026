import os
import uvicorn
import json
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
import certifi

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import Response

# Componentes de MCP
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

# Componentes de Scalekit para Auth
from scalekit import ScalekitClient
from dotenv import load_dotenv

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 15
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

WEATHER_CODE_LABELS = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 71: "Slight snow fall",
    73: "Moderate snow fall", 75: "Heavy snow fall", 95: "Thunderstorm"
}

CURRENT_VARIABLES = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"]

"""
SERVIDOR MCP SEGURO CON OAUTH 2.1 (SCALEKIT)
--------------------------------------------
Este script expone el servidor MCP de CLIMA a Internet usando HTTP (SSE).
Protegido por Scalekit para que solo Agentes autorizados puedan ver el clima.
"""

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
mcp_app = mcp.sse_app()

async def secure_app(scope, receive, send):
    if scope["type"] == "http":
        request = Request(scope, receive)
        # Protegemos los endpoints de MCP
        if request.url.path in ["/sse", "/messages"]:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                response = Response(status_code=401, content="Falta el token Bearer")
                return await response(scope, receive, send)
            
            token = auth_header.split(" ")[1]
            try:
                is_valid = sc.validate_access_token(token)
                if not is_valid:
                    response = Response(status_code=401, content="El token es inválido")
                    return await response(scope, receive, send)
            except Exception as e:
                response = Response(status_code=401, content=f"Autenticación fallida: {e}")
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

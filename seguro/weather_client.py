import os
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client
from scalekit import ScalekitClient
from dotenv import load_dotenv

# Cargar credenciales
load_dotenv()
env_url = os.getenv("SCALEKIT_ENVIRONMENT_URL")
client_id = os.getenv("SCALEKIT_CLIENT_ID")
client_secret = os.getenv("SCALEKIT_CLIENT_SECRET")

async def run_weather_client():
    print("======================================================")
    print("   CLIENTE MCP CLIMA (CON SEGURIDAD SCALEKIT)")
    print("======================================================\n")

    print("🔐 Paso 1: Obteniendo token de autorización en la nube...")
    # Este script actúa como un Agente automatizado, no como una persona:
    # usa client credentials (M2M) para conseguir su propio token, sin login
    # humano de por medio. Para el flujo con un usuario real autenticándose
    # con GitHub, ver github_login/app.py.
    sc = ScalekitClient(env_url, client_id, client_secret)
    token = sc.get_client_access_token()
    
    print("✅ Token obtenido exitosamente.")
    print("Ocultando token por seguridad (***...***)\n")

    # Usamos HTTP SSE para conectarnos al servidor
    server_url = "http://localhost:8000/sse"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\nIntentando conectar a {server_url} de forma segura...")
    
    try:
        # El bloque sse_client maneja la conexión HTTP de larga duración
        async with sse_client(url=server_url, headers=headers) as streams:
            # Inicializamos la sesión MCP
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("✅ ¡Conexión MCP Autorizada y Establecida!\n")
                
                # Pedimos listar herramientas para confirmar qué hay
                tools = await session.list_tools()
                print("Herramientas disponibles descubiertas:")
                for t in tools.tools:
                    print(f" - {t.name}: {t.description}")
                
                # Ejecutamos el clima para Bogotá (Lat: 4.6097, Lon: -74.0817)
                print("\n☁️ Ejecutando 'get_weather' para Bogotá...")
                result = await session.call_tool(
                    "get_weather", 
                    arguments={"latitude": 4.6097, "longitude": -74.0817}
                )
                
                # Imprimimos el resultado que devuelve el servidor
                for content in result.content:
                    if content.type == "text":
                        print(f"\nRespuesta del MCP:\n{content.text}")
                        
    except Exception as e:
        print(f"\n❌ Error de Conexión: {e}")
        print("Si el servidor dice 'Unauthorized', tu token expiró o es inválido.")
        print("Asegúrate de que 'uv run secure-mcp' está corriendo en otra terminal.")

if __name__ == "__main__":
    # uv run python weather_client.py
    asyncio.run(run_weather_client())

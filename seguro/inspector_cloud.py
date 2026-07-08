import os
import subprocess
from scalekit import ScalekitClient
from dotenv import load_dotenv

# Cargar credenciales
load_dotenv()
env_url = os.getenv("SCALEKIT_ENVIRONMENT_URL")
client_id = os.getenv("SCALEKIT_CLIENT_ID")
client_secret = os.getenv("SCALEKIT_CLIENT_SECRET")

def main():
    print("======================================================")
    print("   INSPECTOR MCP EN LA NUBE (RENDER + SCALEKIT)")
    print("======================================================\n")
    
    print("🔐 Paso 1: Obteniendo token de autorización...")
    # Igual que weather_client.py, este puente usa client credentials (M2M):
    # el propio script se autentica como Agente para poder inspeccionar el
    # servidor, sin representar a ningún usuario humano en particular.
    sc = ScalekitClient(env_url, client_id, client_secret)
    token = sc.get_client_access_token()
    print("✅ Token obtenido exitosamente.\n")

    server_url = "https://mcp2026.onrender.com/sse"
    print(f"🚀 Iniciando Inspector oficial conectado a {server_url}...")
    print("⚠️  Abre la URL (http://localhost:5173) en tu navegador y dale a 'Connect'.\n")

    # Llamamos a npx pasándole los argumentos de SSE y el Header de seguridad
    subprocess.run([
        "npx", "-y", "@modelcontextprotocol/inspector",
        "--transport", "sse",
        "--server-url", server_url,
        "--header", f"Authorization: Bearer {token}"
    ])

if __name__ == "__main__":
    main()

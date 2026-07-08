"""
LOGIN DE USUARIO CON GITHUB (SCALEKIT)
---------------------------------------
seguro/secure_mcp.py ya protege el MCP, pero solo con tokens de máquina
(client credentials): un Agente se autentica a sí mismo, no hay ningún
humano detrás. Esta app añade el flujo que faltaba: un usuario real inicia
sesión con su cuenta de GitHub, Scalekit lo autentica y registra, y el
token resultante sirve exactamente igual para llamar al MCP seguro
(ver el comentario en secure_mcp.py: ambos tipos de token son válidos).

Flujo (Authorization Code, RFC 6749 + OIDC):
1. GET /login       -> redirige al usuario a la pantalla de login de GitHub
                        que gestiona Scalekit (nosotros nunca vemos su
                        contraseña).
2. GET /callback    -> Scalekit devuelve un "code" de un solo uso; lo
                        cambiamos por los tokens del usuario y lo registramos
                        localmente en usuarios_registrados.json.

Nota de seguridad: no implementamos PKCE (code_challenge/code_verifier)
porque este backend es un "cliente confidencial": guarda el
SCALEKIT_CLIENT_SECRET en el servidor y nunca lo expone al navegador. PKCE
es indispensable para clientes públicos (SPA, apps móviles) que no pueden
guardar un secreto; aquí el secreto + el parámetro `state` (que sí usamos,
para evitar CSRF) son suficientes.
"""

import json
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from scalekit import ScalekitClient
from scalekit.common.scalekit import AuthorizationUrlOptions, CodeAuthenticationOptions

load_dotenv()

env_url = os.getenv("SCALEKIT_ENVIRONMENT_URL", "https://tu_entorno.scalekit.com")
client_id = os.getenv("SCALEKIT_CLIENT_ID", "tu_client_id_aqui")
client_secret = os.getenv("SCALEKIT_CLIENT_SECRET", "tu_client_secret_aqui")
# Debe coincidir EXACTO con el Redirect URI configurado para la conexión de
# GitHub en el Dashboard de Scalekit.
redirect_uri = os.getenv("SCALEKIT_REDIRECT_URI", "http://localhost:8787/callback")

sc = ScalekitClient(env_url, client_id, client_secret)

app = FastAPI(title="Login con GitHub (Scalekit)")

# Registro local de usuarios autenticados, solo para fines didácticos/auditoría.
# Scalekit ya guarda a estos usuarios en su propio directorio; este archivo es
# una copia visible en el proyecto para la demo (por eso está en .gitignore).
REGISTRO_PATH = Path(__file__).parent / "usuarios_registrados.json"

# `state` pendientes por resolver: protegen contra CSRF verificando que el
# callback corresponde a un /login que nosotros mismos iniciamos.
_PENDING_STATES: dict[str, float] = {}
_STATE_TTL_SECONDS = 300


def _registrar_usuario(user: dict[str, Any], connection_id: str | None) -> None:
    """Guarda (o actualiza) al usuario autenticado en usuarios_registrados.json."""
    registrados: list[dict[str, Any]] = []
    if REGISTRO_PATH.exists():
        registrados = json.loads(REGISTRO_PATH.read_text(encoding="utf-8"))

    sub = user.get("sub") or user.get("email")
    entrada = {
        "sub": sub,
        "email": user.get("email"),
        "nombre": user.get("name") or user.get("preferred_username"),
        "connection_id": connection_id,
        "ultimo_login": datetime.now(timezone.utc).isoformat(),
    }

    # Un usuario puede volver a loguearse; reemplazamos su entrada anterior
    # en vez de acumular duplicados.
    registrados = [r for r in registrados if r.get("sub") != sub]
    registrados.append(entrada)

    REGISTRO_PATH.write_text(
        json.dumps(registrados, indent=2, ensure_ascii=False), encoding="utf-8"
    )


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <html><body style="font-family: sans-serif; text-align:center; margin-top: 15vh;">
      <h1>MCP seguro &mdash; Login de usuario</h1>
      <p>Inicia sesión con tu cuenta de GitHub para obtener un token de acceso
      personal al servidor MCP protegido con Scalekit.</p>
      <p><a href="/login" style="font-size:1.2rem;">Iniciar sesión con GitHub</a></p>
    </body></html>
    """


@app.get("/login")
def login() -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    _PENDING_STATES[state] = time.time()

    options = AuthorizationUrlOptions()
    options.provider = "github"
    options.state = state

    authorization_url = sc.get_authorization_url(redirect_uri, options)
    return RedirectResponse(authorization_url)


@app.get("/callback", response_class=HTMLResponse)
def callback(request: Request) -> str:
    params = request.query_params

    error = params.get("error")
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"GitHub/Scalekit devolvió un error: {error} "
            f"({params.get('error_description', 'sin descripción')})",
        )

    code = params.get("code")
    state = params.get("state")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Falta 'code' o 'state' en la respuesta de Scalekit.")

    issued_at = _PENDING_STATES.pop(state, None)
    if issued_at is None:
        raise HTTPException(status_code=400, detail="El parámetro 'state' no es válido o ya fue usado.")
    if time.time() - issued_at > _STATE_TTL_SECONDS:
        raise HTTPException(status_code=400, detail="El login tardó demasiado y expiró; intenta de nuevo.")

    try:
        result = sc.authenticate_with_code(code, redirect_uri, CodeAuthenticationOptions())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"No se pudo validar el login con Scalekit: {exc}") from exc

    user = result["user"]
    _registrar_usuario(user, result.get("connection_id"))

    token = result["access_token"]
    token_preview = f"{token[:12]}...{token[-6:]}" if len(token) > 24 else "***"

    return f"""
    <html><body style="font-family: sans-serif; max-width: 720px; margin: 10vh auto;">
      <h1>✅ Sesión iniciada con GitHub</h1>
      <p><strong>Usuario:</strong> {user.get('name') or user.get('preferred_username')}
         ({user.get('email', 'sin email público')})</p>
      <p>Este usuario quedó registrado en <code>usuarios_registrados.json</code>
      y en el directorio de Scalekit.</p>
      <p><strong>Token de acceso (recortado por seguridad):</strong>
         <code>{token_preview}</code></p>
      <p>Úsalo como header contra el MCP seguro, igual que un token de máquina:</p>
      <pre style="background:#111;color:#dceaff;padding:16px;border-radius:8px;overflow-x:auto;">
Authorization: Bearer {token}
      </pre>
      <p>Por ejemplo, con Claude Code:</p>
      <pre style="background:#111;color:#dceaff;padding:16px;border-radius:8px;overflow-x:auto;">
claude mcp add --transport http secure-mcp \\
  https://tu-dominio.com/sse \\
  --header "Authorization: Bearer {token}"
      </pre>
    </body></html>
    """


def main() -> None:
    port = int(os.getenv("GITHUB_LOGIN_PORT", "8787"))
    print("Iniciando login de usuario con GitHub (vía Scalekit)...")
    print(f"Abre http://localhost:{port} en tu navegador y haz clic en 'Iniciar sesión con GitHub'.")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

"""
Script interactivo para configurar la autenticación de Google APIs.
Permite autorizar tu cuenta corporativa de Google para:
- Crear eventos en Google Calendar (scope: calendar.events)
- Enviar correos por Gmail API (scope: gmail.send)
Guarda automáticamente el Refresh Token en backend/.env.
"""

import json
import os
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.send",
]

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


def update_env_file(key: str, value: str):
    if not ENV_FILE.exists():
        lines = []
    else:
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f'{key}="{value}"')
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f'{key}="{value}"')

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"✓ Actualizado {key} en backend/.env")


def auth_with_credentials_json(credentials_path: str):
    print(f"\nIniciando flujo de autorización desde: {credentials_path}")
    
    with open(credentials_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    client_type = list(data.keys())[0]
    info = data[client_type]
    
    # Preparar configuración compatible con InstalledAppFlow
    client_config = {
        "installed": {
            "client_id": info["client_id"],
            "client_secret": info["client_secret"],
            "auth_uri": info.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": info.get("token_uri", "https://oauth2.googleapis.com/token"),
            "redirect_uris": ["http://localhost:8080/"],
        }
    }

    try:
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
        creds = flow.run_local_server(
            host="localhost",
            port=8080,
            prompt="consent",
            access_type="offline"
        )

        print("\n" + "=" * 60)
        print("¡AUTORIZACIÓN EXITOSA CON GOOGLE!")
        print("=" * 60)

        update_env_file("GOOGLE_AUTH_MODE", "oauth2")
        if creds.client_id:
            update_env_file("GOOGLE_CLIENT_ID", creds.client_id)
        if creds.client_secret:
            update_env_file("GOOGLE_CLIENT_SECRET", creds.client_secret)
        if creds.refresh_token:
            update_env_file("GOOGLE_REFRESH_TOKEN", creds.refresh_token)

        print("\nTodo listo: las credenciales reales de Google han quedado configuradas en backend/.env.")
    except Exception as exc:
        print(f"\nError durante la autorización: {exc}")
        print("\nNOTA: Si Google muestra 'redirect_uri_mismatch', asegúrate de que en Google Cloud Console:")
        print("1. En tu ID de cliente OAuth ('Web application'), agrega 'http://localhost:8080/' en")
        print("   'URIs de redireccionamiento autorizados'.")
        print("2. O crea un nuevo ID de cliente de tipo 'Aplicación de escritorio' (Desktop app).")


def main():
    print("=" * 60)
    print("CONFIGURADOR DE CREDENCIALES GOOGLE (CALENDAR & GMAIL)")
    print("=" * 60)

    credentials_path = BACKEND_DIR / "credentials.json"
    if credentials_path.exists():
        auth_with_credentials_json(str(credentials_path))
    else:
        print(f"No se encontró {credentials_path}")


if __name__ == "__main__":
    main()

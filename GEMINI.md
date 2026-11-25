# Reglas del Proyecto (GEMINI.md)

Consulta y respeta las reglas completas documentadas en [AGENTS.md](file:///Users/tec-sebastianrebolledo/Library/CloudStorage/GoogleDrive-sebastian.rebolledo@grupotecfluid.com/Mi%20unidad/Desarrollo%20de%20aplicaciones/AGENTS.md).

### Resumen de Reglas Clave:
1. **Frontend**: Next.js (React) con CSS nativo / CSS Modules.
2. **Backend**: Python con FastAPI (Pydantic, Uvicorn, Tipado estricto).
3. **Google APIs**: Google Auth (OAuth2), Calendar API, Gmail API con bibliotecas oficiales de Google (`google-api-python-client`, `google-auth`).
4. **Política de Cero Dependencias Innecesarias**: Usar `fetch` nativo, módulos estándar de Python y APIs nativas de JS/Web antes de cualquier paquete externo.
5. **Seguridad**: Credenciales y tokens siempre en `.env` (nunca en código), principio de mínimos privilegios en scopes OAuth.

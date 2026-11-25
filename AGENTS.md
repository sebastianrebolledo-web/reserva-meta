# Reglas del Proyecto

Este documento define los estándares arquitectónicos, convenciones de desarrollo y directrices obligatorias para este proyecto.

---

## 1. Stack Tecnológico

- **Frontend**: **Next.js** (React)
  - Enrutamiento mediante App Router o Pages Router según la arquitectura definida.
  - Soporte para Server-Side Rendering (SSR) y Client Components según la necesidad.
  - Estilos con **CSS puro / CSS Modules** para mantener control total y evitar dependencias redundantes.
- **Backend**: **Python (FastAPI)**
  - Tipado estricto y validación de esquemas con **Pydantic**.
  - Servidor ASGI asíncrono con **Uvicorn**.
  - Arquitectura modular (routers, services, schemas, core/config).
- **Integraciones Google Cloud & APIs**:
  - **Google Auth**: Flujo OAuth 2.0 seguro (Auth Code Flow), manejo de sesiones, almacenamiento seguro de refresh tokens y principio de privilegios mínimos en scopes.
  - **Google Calendar API**: Gestión, sincronización y consulta de calendarios/eventos.
  - **Gmail API**: Lectura, búsqueda, composición y envío de correos, gestión de etiquetas y metadatos.

---

## 2. Política de Dependencias Estrictas ("No Dependencias Innecesarias")

- **Máxima ligereza**: Solo se permiten paquetes esenciales y directamente requeridos para el funcionamiento del sistema.
- **Preferir APIs Nativas**:
  - En el Frontend (Next.js/JS/TS): Usar `fetch` nativo del navegador/Next.js en lugar de librerías HTTP externas como `axios`. Usar `Intl` y `Date` nativo en lugar de `moment.js` o `dayjs` a menos que se requiera cálculo de zonas horarias complejo no cubierto por JS moderno.
  - En el Backend (Python): Usar módulos de la librería estándar (`datetime`, `os`, `json`, `pathlib`, `typing`, `dataclasses`, `asyncio`) antes de buscar librerías de terceros.
- **Librerías de Google**:
  - Utilizar exclusivamente las bibliotecas cliente oficiales recomendadas:
    - `google-api-python-client`
    - `google-auth` / `google-auth-oauthlib` / `google-auth-httplib2`
- **Criterio de aprobación**: Antes de proponer o instalar una dependencia (`npm install` o `pip install`), se debe justificar técnicamente por qué la funcionalidad no puede resolverse con el runtime nativo o los frameworks base existentes.

---

## 3. Seguridad y Manejo de Credenciales

- **Cero secretos en el código**: Queda estrictamente prohibido hardcodear API Keys, Client IDs, Client Secrets, tokens de acceso o refresh tokens.
- **Variables de Entorno**:
  - Frontend: Variables públicas prefijadas con `NEXT_PUBLIC_` únicamente si no exponen datos sensibles.
  - Backend: Uso de `.env` gestionado mediante `pydantic-settings` o variables de entorno del sistema.
  - Los archivos `.env`, `.env.local`, `credentials.json`, `token.json` o cualquier archivo de cuenta de servicio (`service-account.json`) deben estar incluidos en `.gitignore`.
- **Scopes Mínimos**: Al solicitar permisos a las APIs de Google (Auth, Calendar, Gmail), solicitar exclusivamente los scopes indispensables para la tarea (ej. preferir `calendar.events.readonly` sobre `calendar` completo si solo se requiere lectura).

---

## 4. Arquitectura y Separación de Responsabilidades

- **Frontend (`/frontend`)**:
  - Encargado exclusivamente de la interfaz de usuario, experiencia interactiva, presentación visual y gestión de estado de cliente.
  - Las llamadas a las APIs de Google con credenciales de servidor o procesamiento sensible deben delegarse al backend FastAPI.
- **Backend (`/backend`)**:
  - Expone APIs REST documentadas automáticamente vía OpenAPI/Swagger (`/docs`).
  - Manejo seguro de la lógica de intercambio de códigos OAuth 2.0 y llamadas a los servicios de Google (Gmail, Calendar).
  - Manejo consistente de errores HTTP (400, 401, 403, 404, 500) devolviendo respuestas estructuradas en formato JSON (`{"detail": "..."}`).

---

## 5. Calidad de Código y Estilo

- **Tipado Fuerte**:
  - TypeScript en Next.js con interfaces/tipos explícitos para props y respuestas de API.
  - Type Hints obligatorios en Python (PEP 484) para argumentos y valores de retorno de funciones.
- **Diseño y Estética**:
  - Interfaces limpias, modernas y profesionales con CSS nativo estructurado.
  - Estados claros de carga (`loading`), error (`error`) y contenido vacío (`empty states`).
- **Documentación y Mantenibilidad**:
  - Comentarios concisos explicando el "por qué" de decisiones técnicas, no el "qué" evidente.
  - Archivos `.env.example` en frontend y backend con las variables requeridas sin valores sensibles reales.

# Guía de Despliegue en la Web (Grupo Tecfluid)

Este documento detalla las opciones para implementar la aplicación en la web con una URL accesible por toda la compañía.

---

## 🔍 ¿Por qué ocurrió el error `ERR_CONNECTION_REFUSED` en `localhost`?

`ERR_CONNECTION_REFUSED` indica que en ese momento **no había ningún servidor ejecutándose en tu computador** escuchando en los puertos `3000` o `8000`.

- `localhost:3000` solo funciona en tu propio equipo y requiere que tengas la terminal abierta ejecutando la aplicación.
- Para que **cualquier colaborador de la empresa pueda acceder desde su equipo sin depender de tu computador**, la aplicación debe publicarse en la web en un servidor o servicio en la nube.

---

## 🚀 Opción 1: Google Cloud Run (Recomendada para Grupo Tecfluid)

Dado que la empresa ya opera con el ecosistema de Google Workspace (`@grupotecfluid.com`), Google Calendar y Gmail, **Google Cloud Run** es la plataforma ideal:
- **Serverless**: Costo $0 o centavos (escala a cero cuando no se usa).
- **HTTPS Automático**: Te entrega una URL pública segura como `https://tecfluid-vr-frontend-xxxx.a.run.app`.
- **Dominio Corporativo**: Se puede mapear a un subdominio institucional como `reservas.grupotecfluid.com`.

### Pasos para desplegar:
1. Asegúrate de tener instalado el CLI de Google Cloud (`gcloud`) o usa [Google Cloud Shell](https://shell.cloud.google.com).
2. Autentica tu cuenta corporativa:
   ```bash
   gcloud auth login
   gcloud config set project <ID_DEL_PROYECTO_GCP>
   ```
3. Ejecuta el script automatizado que hemos preparado:
   ```bash
   ./deploy_cloud_run.sh
   ```
El script compilará ambos contenedores y te devolverá la **URL pública final** para compartir con la empresa.

---

## ⚡ Opción 2: Compartir Inmediatamente Hoy (Túnel Seguro Cloudflare / ngrok)

Si necesitas compartir la aplicación con colegas **ahora mismo** para una demostración sin esperar configuración de servidores en la nube:

1. Inicia el Backend en una terminal:
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn app.main:app --reload --port 8000
   ```

2. Inicia el Frontend en otra terminal:
   ```bash
   cd frontend
   npm run dev
   ```

3. En una tercera terminal, crea una URL pública segura con Cloudflare (gratis y sin registro):
   ```bash
   npx cloudflared tunnel --url http://localhost:3000
   ```
Cloudflare te generará una URL pública segura como `https://random-name.trycloudflare.com` que puedes enviar por chat o correo a cualquier compañero de Tecfluid.

---

## 🐳 Opción 3: Servidor Corporativo Interno o VPS (Docker Compose)

Si Grupo Tecfluid dispone de una máquina virtual o servidor interno en su red:

1. Clona el proyecto en el servidor.
2. Ejecuta:
   ```bash
   docker compose up --build -d
   ```
La aplicación quedará corriendo de forma permanente y se reiniciará automáticamente si el servidor se reinicia.
- Frontend: `http://<IP_O_DOMINIO_DEL_SERVIDOR>:3000`
- Backend: `http://<IP_O_DOMINIO_DEL_SERVIDOR>:8000`

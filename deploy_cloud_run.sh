#!/usr/bin/env bash
# ==============================================================================
# Script de Despliegue en Google Cloud Run - Grupo Tecfluid
# Proyecto: reserva-metaquest-tecfluid
#
# PRERREQUISITOS:
#   1. gcloud CLI instalado y autenticado: gcloud auth login
#   2. Los secretos de producción creados en Secret Manager (ver sección 0)
#   3. Ejecutar desde la RAÍZ del proyecto: ./deploy_cloud_run.sh
# ==============================================================================

set -euo pipefail

# ──────────────────────────────────────────────
# Configuración del proyecto
# ──────────────────────────────────────────────
REGION="${GCP_REGION:-us-central1}"
PROJECT_ID="${GCP_PROJECT_ID:-reserva-metaquest-tecfluid}"
BACKEND_SERVICE="tecfluid-vr-backend"
FRONTEND_SERVICE="tecfluid-vr-frontend"

echo "=========================================================="
echo "  DESPLIEGUE EN GOOGLE CLOUD RUN - GRUPO TECFLUID"
echo "=========================================================="
echo "✓ Proyecto Google Cloud : $PROJECT_ID"
echo "✓ Región de despliegue  : $REGION"
echo "=========================================================="
echo ""

# ──────────────────────────────────────────────
# PASO 0: Verificar autenticación
# ──────────────────────────────────────────────
echo "0/6. Verificando autenticación con Google Cloud..."
if ! gcloud auth print-identity-token > /dev/null 2>&1; then
  echo "❌ ERROR: No estás autenticado. Ejecuta primero:"
  echo "   gcloud auth login"
  echo "   gcloud config set project $PROJECT_ID"
  exit 1
fi
gcloud config set project "$PROJECT_ID" --quiet
echo "✓ Autenticación confirmada."

# ──────────────────────────────────────────────
# PASO 1: Habilitar APIs requeridas
# ──────────────────────────────────────────────
echo ""
echo "1/6. Habilitando APIs de Google Cloud..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  --project "$PROJECT_ID" --quiet
echo "✓ APIs habilitadas."

# ──────────────────────────────────────────────
# PASO 2: Crear secretos en Secret Manager (solo si no existen)
# Los secretos se leen desde el .env local de backend para el primer despliegue.
# ──────────────────────────────────────────────
echo ""
echo "2/6. Verificando secretos en Secret Manager..."

create_secret_if_absent() {
  local secret_name="$1"
  local secret_value="$2"
  if ! gcloud secrets describe "$secret_name" --project "$PROJECT_ID" > /dev/null 2>&1; then
    echo "   Creando secreto: $secret_name"
    echo -n "$secret_value" | gcloud secrets create "$secret_name" \
      --data-file=- \
      --project "$PROJECT_ID" \
      --replication-policy="automatic" \
      --quiet
    echo "   ✓ Secreto '$secret_name' creado."
  else
    echo "   ✓ Secreto '$secret_name' ya existe (no sobreescrito)."
  fi
}

# Leer valores del .env local para poblar Secret Manager la primera vez
if [ -f "./backend/.env" ]; then
  # shellcheck disable=SC1091
  set -o allexport; source ./backend/.env; set +o allexport
  create_secret_if_absent "vr-google-client-secret"  "${GOOGLE_CLIENT_SECRET:-}"
  create_secret_if_absent "vr-google-refresh-token"   "${GOOGLE_REFRESH_TOKEN:-}"
  create_secret_if_absent "vr-secret-key"             "${SECRET_KEY:-}"
  create_secret_if_absent "vr-admin-password"         "${ADMIN_PASSWORD:-}"
else
  echo "   ⚠ ADVERTENCIA: No se encontró backend/.env. Asegúrate de que los secretos ya existen en Secret Manager."
fi

# ──────────────────────────────────────────────
# PASO 3: Build y Deploy del Backend (FastAPI)
# ──────────────────────────────────────────────
echo ""
echo "3/6. Construyendo imagen de Backend en Cloud Build..."
gcloud builds submit ./backend \
  --tag "gcr.io/$PROJECT_ID/$BACKEND_SERVICE" \
  --project "$PROJECT_ID"

echo "     Desplegando Backend en Cloud Run..."
gcloud run deploy "$BACKEND_SERVICE" \
  --image "gcr.io/$PROJECT_ID/$BACKEND_SERVICE" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --set-env-vars "ENVIRONMENT=production,PORT=8080,DATABASE_URL=/app/data/metaquest.db,GOOGLE_AUTH_MODE=oauth2,GOOGLE_CLIENT_ID=1020994005675-p9f6k1qm30it29o3aasjjep665mhhtm8.apps.googleusercontent.com,GOOGLE_CALENDAR_ID=primary,GMAIL_SENDER_EMAIL=soporteti@grupotecfluid.com,CORPORATE_DOMAIN=grupotecfluid.com,IT_SUPPORT_EMAIL=soporteti@grupotecfluid.com,ADMIN_EMAIL=soporteti@grupotecfluid.com,JWT_EXPIRE_HOURS=8,ALLOWED_ORIGINS=*" \
  --set-secrets "GOOGLE_CLIENT_SECRET=vr-google-client-secret:latest,GOOGLE_REFRESH_TOKEN=vr-google-refresh-token:latest,SECRET_KEY=vr-secret-key:latest,ADMIN_PASSWORD=vr-admin-password:latest" \
  --quiet

BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format='value(status.url)')

echo "✓ Backend listo en: $BACKEND_URL"

# ──────────────────────────────────────────────
# PASO 4: Build Frontend con la URL del Backend inyectada
# (usa cloudbuild-frontend.yaml para pasar --build-arg correctamente)
# ──────────────────────────────────────────────
echo ""
echo "4/6. Construyendo imagen de Frontend en Cloud Build..."
echo "     NEXT_PUBLIC_API_URL=$BACKEND_URL"
gcloud builds submit . \
  --config cloudbuild-frontend.yaml \
  --substitutions "_NEXT_PUBLIC_API_URL=$BACKEND_URL" \
  --project "$PROJECT_ID"

# ──────────────────────────────────────────────
# PASO 5: Deploy Frontend
# ──────────────────────────────────────────────
echo ""
echo "5/6. Desplegando Frontend en Cloud Run..."
gcloud run deploy "$FRONTEND_SERVICE" \
  --image "gcr.io/$PROJECT_ID/$FRONTEND_SERVICE" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --set-env-vars "NODE_ENV=production,PORT=8080" \
  --quiet

FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format='value(status.url)')

# ──────────────────────────────────────────────
# PASO 6: Ajustar CORS del Backend con la URL real del Frontend
# ──────────────────────────────────────────────
echo ""
echo "6/6. Actualizando CORS del Backend con URL del Frontend..."
gcloud run services update "$BACKEND_SERVICE" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --update-env-vars "FRONTEND_URL=$FRONTEND_URL,ALLOWED_ORIGINS=$FRONTEND_URL,http://localhost:3000" \
  --quiet

# ──────────────────────────────────────────────
# Resultado final
# ──────────────────────────────────────────────
echo ""
echo "=========================================================="
echo "🎉 ¡DESPLIEGUE A NIVEL COMPAÑÍA COMPLETADO CON ÉXITO!"
echo "=========================================================="
echo ""
echo "🌐 URL PÚBLICA PARA COMPARTIR EN GRUPO TECFLUID:"
echo "👉  $FRONTEND_URL"
echo ""
echo "⚙️  Documentación de API Backend:"
echo "👉  $BACKEND_URL/docs"
echo ""
echo "=========================================================="
echo "⚠️  ACCIÓN REQUERIDA POST-DESPLIEGUE:"
echo ""
echo "  Agrega la siguiente URL como 'Origen de JavaScript autorizado'"
echo "  y como 'URI de redirección autorizado' en Google Cloud Console:"
echo "  🔗 https://console.cloud.google.com/apis/credentials"
echo ""
echo "  URL a agregar: $FRONTEND_URL"
echo "=========================================================="

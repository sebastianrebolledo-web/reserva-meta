#!/usr/bin/env bash
# ==============================================================================
# Script para iniciar el Backend y Frontend de Meta Quest simultáneamente
# Grupo Tecfluid
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "🚀 INICIANDO SISTEMA DE RESERVAS META QUEST (GRUPO TECFLUID)"
echo "=========================================================="

# 1. Iniciar Backend (FastAPI) en puerto 8000
echo "▶ 1/2 Iniciando Backend en http://localhost:8000 ..."
cd "$DIR/backend"
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 2. Iniciar Frontend (Next.js) en puerto 3000
echo "▶ 2/2 Iniciando Frontend en http://localhost:3000 ..."
cd "$DIR/frontend"
# Asegurar acceso a node/npm si están en ~/.local/node/bin
if [ -d "$HOME/.local/node/bin" ]; then
  export PATH="$HOME/.local/node/bin:$PATH"
fi
npm run dev &
FRONTEND_PID=$!

# Capturar señal de salida para apagar ambos procesos con Ctrl+C
cleanup() {
  echo ""
  echo "🛑 Deteniendo servidores..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

echo ""
echo "=========================================================="
echo "🎉 ¡SERVIDORES ACTIVOS!"
echo "=========================================================="
echo "🌐 Aplicativo Web (Portal):"
echo "👉 http://localhost:3000"
echo ""
echo "⚙️  Documentación API (Swagger):"
echo "👉 http://localhost:8000/docs"
echo "=========================================================="
echo "Presiona Ctrl + C en esta terminal para detener los servidores."
echo ""

wait

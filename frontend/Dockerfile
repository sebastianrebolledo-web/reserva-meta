# Etapa 1: Dependencias
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Etapa 2: Build
# NOTA: No se necesita NEXT_PUBLIC_API_URL en build time.
# El proxy se configura en next.config.ts con BACKEND_INTERNAL_URL en runtime.
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Etapa 3: Runtime
FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
ENV PORT=8080
# BACKEND_INTERNAL_URL se inyecta en Cloud Run al momento del deploy (runtime).
# El servidor Next.js usa esta variable para hacer proxy de /api/v1/* al FastAPI backend.
ENV BACKEND_INTERNAL_URL=http://localhost:8000
EXPOSE 8080
CMD ["node", "server.js"]

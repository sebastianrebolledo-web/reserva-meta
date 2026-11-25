# Etapa 1: Builder
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc libffi-dev libssl-dev libjpeg-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Etapa 2: Runtime
FROM python:3.11-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends libjpeg-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY app/ ./app/
RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

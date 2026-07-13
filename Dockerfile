# WISE website + RAG API — one service for Render / Railway / Fly
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Cache bust argument — MUST be before COPY to invalidate Docker layer cache on Render
ARG CACHEBUST=36
ARG BUILD_SHA=dev
ARG BUILD_TIME=unknown

# Backend code (includes data/ corpus, seed/, start.sh)
COPY backend/ /app/

# Frontend static site (HTML/CSS/JS) served by FastAPI
# This COPY layer will be invalidated when CACHEBUST changes
COPY src/ /app/frontend/

# Verify frontend assets were copied correctly
RUN test -f /app/frontend/css/base.css \
    && test -f /app/frontend/css/glass.css \
    && test -f /app/frontend/css/components.css \
    && test -f /app/frontend/css/dark.css \
    && test -f /app/frontend/js/main.js \
    && test -f /app/frontend/js/i18n.js \
    && test -f /app/frontend/js/chat.js \
    && test -f /app/frontend/js/config.js \
    && test -f /app/frontend/pages/index.html \
    && echo "Frontend assets verified OK"

# Deploy stamp — visible at GET /api/version to verify live build
RUN printf '{\n  "service": "wisef",\n  "frontend": "/app/frontend",\n  "build_sha": "%s",\n  "build_time": "%s",\n  "asset_version": "%s"\n}\n' "$BUILD_SHA" "$BUILD_TIME" "$CACHEBUST" > /app/version.json \
    && echo "cachebust=$CACHEBUST" > /app/frontend/.deploy-stamp \
    && test -f /app/start.sh

RUN mkdir -p /app/data/corpus

ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]

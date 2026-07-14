# WISE website + RAG API — one service for Render / Railway / Fly
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Cache bust argument — MUST be before COPY to invalidate Docker layer cache on Render
ARG CACHEBUST=46
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
    && test -f /app/frontend/pages/about.html \
    && test -f /app/frontend/pages/services.html \
    && test -f /app/frontend/pages/partners.html \
    && test -f /app/frontend/pages/contact.html \
    && test -f /app/frontend/pages/blog.html \
    && test -f /app/frontend/pages/en/index.html \
    && test -f /app/frontend/pages/en/about.html \
    && test -f /app/frontend/pages/en/services.html \
    && test -f /app/frontend/pages/en/partners.html \
    && test -f /app/frontend/pages/en/contact.html \
    && test -f /app/frontend/pages/en/blog.html \
    && test -f /app/frontend/assets/data/blog-posts.json \
    && test -f /app/frontend/assets/images/partners/HH_Gerb.svg \
    && test -f /app/frontend/assets/images/partners/usaid.svg \
    && test -f /app/frontend/assets/images/partners/microsoft.svg \
    && test -f /app/frontend/assets/images/partners/p22.png \
    && test -f /app/frontend/assets/images/partners/p28.png \
    && test -f /app/frontend/assets/images/partners/p41.jpg \
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

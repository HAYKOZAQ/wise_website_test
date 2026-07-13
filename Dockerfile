# WISE website + RAG API — one service for Render / Railway / Fly
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Backend code (includes data/ corpus, seed/, start.sh)
COPY backend/ /app/

# Frontend static site (HTML/CSS/JS) served by FastAPI
COPY src/ /app/frontend/

# Deploy stamp — visible at GET /api/version so we can verify the live build.
# CACHEBUST invalidates Docker layer cache when frontend/backend changes (Render sometimes reuses stale COPY layers).
ARG CACHEBUST=32
ARG BUILD_SHA=dev
ARG BUILD_TIME=unknown
RUN printf '{\n  "service": "wisef",\n  "frontend": "/app/frontend",\n  "build_sha": "%s",\n  "build_time": "%s",\n  "asset_version": "%s"\n}\n' "$BUILD_SHA" "$BUILD_TIME" "$CACHEBUST" > /app/version.json \
    && echo "cachebust=$CACHEBUST" > /app/frontend/.deploy-stamp \
    && test -f /app/frontend/css/dark.css \
    && test -f /app/frontend/js/i18n.js \
    && test -f /app/start.sh

RUN mkdir -p /app/data/corpus

ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Fast boot: serve immediately using baked corpus (data/ + seed/).
# Full re-scrape only if FORCE_SCRAPE_ON_BOOT=1 or corpus missing.
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]

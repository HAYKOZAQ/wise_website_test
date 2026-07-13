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

# Deploy stamp — visible at GET /api/version so we can verify the live build
ARG BUILD_SHA=dev
ARG BUILD_TIME=unknown
RUN printf '{\n  "service": "wisef",\n  "frontend": "/app/frontend",\n  "build_sha": "%s",\n  "build_time": "%s",\n  "asset_version": "28"\n}\n' "$BUILD_SHA" "$BUILD_TIME" > /app/version.json

RUN mkdir -p /app/data/corpus

ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Fast boot: serve immediately using baked corpus (data/ + seed/).
# Full re-scrape only if FORCE_SCRAPE_ON_BOOT=1 or corpus missing.
# (Blocking scraper on every deploy was preventing new frontend from going live.)
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]

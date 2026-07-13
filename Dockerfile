# WISE website + RAG API — one service for Render / Railway / Fly
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Backend code
COPY backend/ /app/

# Frontend static site (HTML/CSS/JS) served by FastAPI
COPY src/ /app/frontend/

RUN mkdir -p /app/data/corpus

ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Index MLSA corpus (summaries + ARLIS + PDFs + web), then serve website + API
# Seed under /app/seed is used if live download fails.
CMD sh -c "python scraper.py; python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"

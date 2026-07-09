# WISE RAG API — deploy to Render / Railway / Fly / Cloud Run
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/

# Ensure data directory exists (scraper may fill on first boot)
RUN mkdir -p /app/data/corpus

ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Build index if missing, then start API
CMD sh -c "python scraper.py; python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"

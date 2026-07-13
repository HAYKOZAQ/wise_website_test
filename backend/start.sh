#!/bin/sh
# Fast boot for Render: do NOT block on full ARLIS/PDF scrape.
# Corpus is already baked into the image under /app/data and /app/seed.
set -e
cd /app

if [ "${FORCE_SCRAPE_ON_BOOT}" = "1" ] || [ "${FORCE_SCRAPE_ON_BOOT}" = "true" ]; then
  echo "[start] FORCE_SCRAPE_ON_BOOT set — running scraper before serve"
  python scraper.py || echo "[start] scraper finished with warnings"
elif [ ! -f /app/data/mlsa_programs.json ] && [ ! -f /app/seed/mlsa_programs.json ]; then
  echo "[start] No corpus found — building index once"
  python scraper.py || echo "[start] scraper finished with warnings"
else
  echo "[start] Using existing corpus (skip scrape). Set FORCE_SCRAPE_ON_BOOT=1 to rebuild."
fi

export PORT="${PORT:-8000}"
export HOST="${HOST:-0.0.0.0}"
echo "[start] Serving on ${HOST}:${PORT}"
exec python -m uvicorn main:app --host "${HOST}" --port "${PORT}"

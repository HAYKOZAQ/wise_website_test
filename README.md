---
title: WISE MLSA RAG API
sdk: docker
app_port: 8000
---

# WISE MLSA RAG API

This repository contains the WISE static website and its FastAPI retrieval API.

## Free split deployment

- Cloudflare Pages hosts the Eleventy output from `_site/`.
- Hugging Face Docker Spaces hosts the Python API from the root `Dockerfile`.
- Set `WISEF_API_BASE` in the Cloudflare Pages build environment to the public
  Hugging Face Space URL, for example `https://user-space.hf.space`.
- Set `CORS_ORIGINS` or `WISEF_PAGES_ORIGIN` in the Space to the exact Pages
  origin, for example `https://wisef-website.pages.dev`.

Required Space settings:

- `GEMINI_API_KEY`
- `CORS_ORIGINS` or `WISEF_PAGES_ORIGIN`
- `ADMIN_TOKEN` if remote admin endpoints are needed

Recommended Space variables:

- `USE_LOCAL_EMBEDDER=1`
- `REINGEST_MODE=off`
- `FORCE_SCRAPE_ON_BOOT=0`

Cloudflare Pages build settings:

- Build command: `npm run build`
- Output directory: `_site`
- Build variable: `WISEF_API_BASE=https://user-space.hf.space`

The root README metadata also makes this repository directly usable as a
Hugging Face Docker Space.

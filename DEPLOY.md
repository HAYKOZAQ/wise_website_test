# WISE Deployment

The application has two deployable parts:

- Static Eleventy website: `_site/`
- FastAPI RAG service: `backend/`

## Recommended: Cloudflare Pages + Hugging Face

This avoids Render's 15-minute sleep and gives the API substantially more
memory than a 512 MB container.

### 1. Build the API index

The compact BM25 index is used by Render. The existing FAISS file is preserved
for the full Hugging Face image, where local sentence-transformer queries can
use dense retrieval.

```bat
python backend\build_index.py --sparse-only
```

For a complete refresh from ARLIS, PDFs, and official web pages:

```bat
python backend\build_index.py --force
```

The generated files under `backend/data/index/` are deployment artifacts:

- `chunks.json`
- `bm25.npz`
- `bm25_vocab.json`
- `corpus_hash.txt`
- `faiss.index` when dense indexing was available

### 2. Deploy the API to Hugging Face Spaces

1. Create a new Space with **Docker** as the SDK.
2. Push this repository to the Space. The root `README.md` contains the Space
   metadata and the root `Dockerfile` is the full runtime image.
3. Configure these Space secrets:

   | Key | Value |
   |-----|-------|
   | `GEMINI_API_KEY` | Google AI Studio key for answer generation |
   | `CORS_ORIGINS` | Exact Cloudflare Pages origin |
   | `ADMIN_TOKEN` | Optional token for remote admin endpoints |

4. Configure these variables:

   | Key | Value |
   |-----|-------|
   | `USE_LOCAL_EMBEDDER` | `1` |
   | `REINGEST_MODE` | `off` |
   | `FORCE_SCRAPE_ON_BOOT` | `0` |

The API will be available at `https://YOUR-SPACE.hf.space`. Verify it with
`/api/status` and `/docs`.

### 3. Deploy the website to Cloudflare Pages

Create a Pages project from the same repository with:

| Setting | Value |
|---------|-------|
| Build command | `npm run build` |
| Output directory | `_site` |
| Build variable | `WISEF_API_BASE=https://YOUR-SPACE.hf.space` |

`npm run build` replaces the API marker in the generated `config.js`. The
source file never contains a secret. `wrangler.toml` is included for CLI or
Direct Upload workflows:

```bash
npx wrangler pages deploy _site --project-name wisef-website
```

Set `CORS_ORIGINS` on the Space to the exact Pages origin, for example
`https://wisef-website.pages.dev`. A custom domain can be used instead.

## Render deployment: 512 MB slim service

`render.yaml` uses `Dockerfile`. It is deliberately lightweight and optimized:

- fast multi-stage build compiling Eleventy and serving via FastAPI
- compact NumPy BM25 postings instead of the large Python BM25 object
- no source PDFs, seed snapshots, per-document corpus cache, or ingestion data
- one Uvicorn process and a prebuilt corpus/index

The image supports grounded answer generation through
`GEMINI_API_KEY`, and answers use BM25 retrieval. Dense retrieval is available
in the full Hugging Face image with `USE_LOCAL_EMBEDDER=1`.

To deploy manually on Render:

1. Create a Docker Web Service from this repository.
2. Use `Dockerfile`.
3. Set `GEMINI_API_KEY` in the dashboard only.
4. Set `ADMIN_TOKEN` only if remote admin endpoints are required.
5. Use `/api/status` as the health check.

The same Render URL serves both the static website and API. Leave
`WISEF_API_BASE` empty in that setup so the browser uses same-origin requests.
The service sleeps when idle; that cold start is expected on the free plan.

## Local development

```bat
start_backend.bat
start.bat
```

- Website: `http://localhost:3000`
- API: `http://127.0.0.1:8000`
- Local browser requests use `localApiBase` from `src/js/config.js`.
- Put `GEMINI_API_KEY` in `backend/.env`, never in frontend JavaScript.

## Rebuild and re-ingest

```bat
python backend\build_index.py
python backend\build_index.py --force
reingest.bat
reingest.bat --force
```

The API skips scraping at startup when `backend/data/mlsa_programs.json` is
already present. Ingestion and scheduled re-ingest are intended for a full
runtime or local machine, not the 512 MB slim image.

## API and security variables

| Key | Meaning |
|-----|---------|
| `GEMINI_API_KEY` | Answer generation key; server-side only |
| `ADMIN_TOKEN` | Protects `/api/admin/*` remotely |
| `CORS_ORIGINS` | Comma-separated exact allowed origins; takes precedence |
| `WISEF_PAGES_ORIGIN` | One separate Pages origin when `CORS_ORIGINS` is unset |
| `WISEF_CORS_OPEN` | Explicitly allow `*`; avoid for production |
| `CHAT_RATE_LIMIT` | Chat requests per window, default `20` |
| `USE_LOCAL_EMBEDDER` | Local sentence-transformer dense queries, default `1` |
| `USE_LOCAL_TFIDF` | In-memory fallback when no persisted index, default `1` |
| `LOCAL_EMBED_MODEL` | Default multilingual MiniLM model |
| `LOCAL_EMBED_DEVICE` | `cpu` or `cuda` |
| `USE_RERANKER` | Optional cross-encoder, default `0` |
| `HYBRID_SEMANTIC_WEIGHT` | Dense versus BM25 rank weight, default `0.6` |
| `REINGEST_MODE` | `inprocess`, `windows`, or `off` |
| `REINGEST_INTERVAL_HOURS` | Background interval; use `0` on free services |
| `WISEF_IMPORT_ROOTS` | Allowlisted PDF import directories |
| `CONTACT_WEBHOOK_URL` | Optional contact notification webhook |

## Corpus sources

`backend/scraper.py` combines four layers:

| Layer | Source |
|-------|--------|
| Citizen summaries | Built-in fallback program guides |
| ARLIS legal acts | `backend/arlis_catalog.json` |
| Ministry PDFs | `backend/mlsa_pdf_catalog.json` and `backend/pdfs/` |
| Official web pages | `backend/mlsa_web_ingest.py` |

After changing a source, run `python backend\build_index.py --force` and
redeploy the generated index artifacts.

## Verification

```bash
python -m pytest backend/tests -q
npm.cmd run build
```

Check these endpoints after deployment:

- `GET /api/status`
- `GET /api/version`
- `GET /docs`
- `POST /api/chat`

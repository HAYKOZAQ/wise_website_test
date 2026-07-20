# Deploy WISE site + AI (GitHub Pages + cloud backend)

## Recommended: one Render URL = website + AI

If you only open the Render URL and see **“WISE Social Programs RAG API”**, that is the **backend status page**, not a bug.  
With the latest Docker image, the **same URL** also serves the real website:

| URL | What you get |
|-----|----------------|
| `https://YOUR-APP.onrender.com/` | Full website + chat |
| `https://YOUR-APP.onrender.com/index.html` | Full website + chat |
| `https://YOUR-APP.onrender.com/pages/index.html` | Legacy redirect to `/index.html` |
| `https://YOUR-APP.onrender.com/api` | AI backend status (what you saw) |
| `https://YOUR-APP.onrender.com/api/status` | JSON health |
| `https://YOUR-APP.onrender.com/docs` | API docs |

Chat uses **same origin** automatically (`config.js` leaves `productionApiBase` empty).

---

## Deploy on Render (Docker)

1. [render.com](https://render.com) → **New → Web Service** → this GitHub repo  
2. **Runtime:** Docker · **Dockerfile:** repo root  
3. **Environment** (dashboard only — never commit secrets):

   | Key | Value |
   |-----|--------|
   | `GEMINI_API_KEY` | from [Google AI Studio](https://aistudio.google.com/apikey) |

4. Deploy → open: `https://YOUR-APP.onrender.com/`  
5. Use **Ask us** chat (green “ready” when API is up)

**Manual deploy:** Render dashboard → **Manual Deploy → Deploy latest commit** after you push.

---

## Option B: GitHub Pages (site) + Render (API only)

The frontend is now built with **Eleventy**. Publish the generated `_site/` folder
(GitHub Actions, `gh-pages`, or any static host). The Render Docker image builds
`_site/` automatically.

1. Site: `https://YOURUSER.github.io/REPO/` (serve the built `_site/` output)  
2. API: Render Docker as above  
3. In `src/js/config.js` set:

```js
productionApiBase: 'https://YOUR-APP.onrender.com'
```

4. Push so GitHub Pages rebuilds. **Never put the API key in config.js.**

---

## Test

1. Site: `…/` or `…/index.html` — full design + chat  
2. API: `…/api/status` — `"status":"ready"`  
3. Docs: `…/docs`

---

## Free tier / 512 MB deployment (Render, Railway, Fly Hobby)

The default `Dockerfile` installs `torch` + `sentence-transformers` and builds embeddings at runtime. That needs **>1 GB RAM** and will crash on a 512 MB free container.

Use the **slim runtime** instead:

1. **Pre-build the search index locally** (one-time, needs ~600 MB RAM):

   ```bat
   cd backend
   python -m venv .venv-build
   .venv-build\Scripts\activate
   pip install -r requirements.txt
   python scraper.py --force
   deactivate
   ```

   This writes `backend/data/index/` (FAISS + BM25 + chunks).

2. **Commit the index** to git:

   ```bash
   git add backend/data/index/
   git commit -m "chore(index): pre-build FAISS+BM25 index for slim runtime"
   git push
   ```

3. On Render / Railway / Fly use **`Dockerfile.slim`** and set:

   | Key | Value |
   |-----|-------|
   | `GEMINI_API_KEY` | from [Google AI Studio](https://aistudio.google.com/apikey) |
   | `USE_LOCAL_EMBEDDER` | `0` (already the default in `Dockerfile.slim`) |

   The slim image has **no torch / sentence-transformers / tensorflow** at runtime and fits in ~512 MB RAM.

### Query embeddings on the free tier

- **Best quality:** keep `GEMINI_API_KEY` set. Queries are embedded via the free Gemini API and matched against the pre-built index.
- **Fully offline / zero API cost:** unset `GEMINI_API_KEY`. Retrieval falls back to BM25 keyword search only (still works, slightly lower semantic recall).

## Local development (unchanged)

```bat
start_backend.bat
start.bat
```

- Frontend: `localhost` → uses `http://127.0.0.1:8000`  
- Secret: `backend/.env` (gitignored) with `GEMINI_API_KEY=...`

---

## MLSA programs in the AI (PDFs + laws + web)

The RAG corpus is built by `backend/scraper.py` from **four layers**:

| Layer | Source | How to expand |
|-------|--------|----------------|
| Citizen summaries | Built-in program guides | Edit `backend/scraper.py` `FALLBACK_PROGRAMS` |
| ARLIS legal acts | `backend/arlis_catalog.json` | Add `act_id` + URLs |
| Ministry PDFs | `backend/mlsa_pdf_catalog.json` + `backend/pdfs/*.pdf` | Drop PDFs or add catalog URLs |
| Official web pages | `backend/mlsa_web_ingest.py` | Add pages to `PROGRAM_PAGES` |

Rebuild index:

```bat
cd backend
python scraper.py
python scraper.py --force
```

Optional env:

| Key | Meaning |
|-----|---------|
| `FORCE_EMBED=1` | Build full vector embeddings (slow, better search) |
| `CHAT_RATE_LIMIT` | Max chat requests per IP per window (default 20) |
| `CORS_ORIGINS` | Comma-separated origins, or `*` |
| `CONTACT_WEBHOOK_URL` | Optional webhook for contact form |
| `ADMIN_TOKEN` | Secret for `/api/admin/*` (required when set, even on localhost) |
| `REINGEST_MODE` | `inprocess` (default) \| `windows` \| `off` — only one schedule path |
| `REINGEST_INTERVAL_HOURS` | e.g. `24` — in-process schedule (ignored if mode=windows) |
| `REINGEST_ON_START` | `1` to re-ingest once when API starts (with scheduler) |
| `REINGEST_FORCE` | `1` force re-download on scheduled runs |
| `CORS_ORIGINS` | Explicit list, or set `WISEF_CORS_OPEN=1` for `*` |
| `USE_LOCAL_TFIDF` | Default `1` — offline TF–IDF vectors when cloud embed skipped |
| `USE_LOCAL_EMBEDDER` | Default `1` — own local sentence-transformer embeddings (no Google/Ollama) |
| `LOCAL_EMBED_MODEL` | Default `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| `LOCAL_EMBED_DEVICE` | `cpu` (default) or `cuda` if GPU available |
| `USE_RERANKER` | Default `0` — enable cross-encoder re-ranking for better precision |
| `HYBRID_SEMANTIC_WEIGHT` | Default `0.6` — weight of dense vs. BM25 in hybrid scoring |
| `QUERY_EXPANSION` | Default `0` — ask the LLM to rewrite the query for better recall |
| `FORCE_EMBED=1` | Build dense embedding cache (slow) — uses local embedder first |

Seed snapshot (offline-friendly) is written to `backend/seed/mlsa_programs.json` after a successful scrape.

---

## Bulk PDF import + scheduled re-ingest

### Import a folder of ministry PDFs

```bat
import_pdfs.bat "D:\MLSA_PDFs"
```

Or:

```bat
python backend\bulk_import_pdfs.py "D:\MLSA_PDFs"
python backend\reingest.py
```

### Manual full re-ingest

```bat
reingest.bat
reingest.bat --force
```

### While the server is running (hot reload)

```bat
curl -X POST http://127.0.0.1:8000/api/admin/reingest -H "Content-Type: application/json" -d "{\"force\":false}"
curl http://127.0.0.1:8000/api/admin/ingest-status
curl -X POST http://127.0.0.1:8000/api/admin/reload
```

### Windows daily schedule

```powershell
.\install_scheduled_reingest.ps1
.\install_scheduled_reingest.ps1 -Hour 3 -Minute 15
.\install_scheduled_reingest.ps1 -Uninstall
```

### In-process schedule (Render / Docker)

Set `REINGEST_INTERVAL_HOURS=24` and `ADMIN_TOKEN=...` in the host environment.

---

## Security checklist

| Do | Don’t |
|----|--------|
| Set `GEMINI_API_KEY` only on Render/Railway | Commit `.env` or keys to GitHub |
| Put only the **public API URL** in `config.js` | Put API keys in frontend JS |
| Keep `.env` in `.gitignore` | Upload `.env` to GitHub Pages |

---

## Free-tier note (Render)

Free services **sleep** after idle time. First chat after sleep can take 30–60s while the server wakes up. That is normal.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| “Server offline” on live site | `productionApiBase` empty or wrong; set it and push |
| CORS error in browser console | Confirm API URL is https and service is up |
| 502 / cold start | Wait and retry; check Render logs |
| Empty answers / 500 | `GEMINI_API_KEY` missing on host → add in Environment |
| Status ok but no programs | First boot runs `scraper.py`; check logs for ARLIS download |
| `Keras 3` error from `transformers` | Install `tf-keras` (only needed when TensorFlow is present) or set `TF_USE_LEGACY_KERAS=1` |
| FAISS `_ARRAY_API not found` | `faiss-cpu` wheel mismatched with NumPy; use the versions pinned in `requirements.txt` |

### CPU-only PyTorch

If you want the smaller CPU wheel instead of the default CUDA wheel:

```bash
pip install torch==2.8.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
```

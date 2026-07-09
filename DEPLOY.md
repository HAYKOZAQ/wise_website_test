# Deploy WISE site + AI (GitHub Pages + cloud backend)

## Why AI fails on GitHub Pages

| Piece | GitHub Pages | Needs |
|--------|----------------|--------|
| Website HTML/CSS/JS | ✅ works | static files only |
| Python FastAPI RAG | ❌ **cannot run** | always-on server |
| `.env` / `GEMINI_API_KEY` | ❌ **do not upload** | secret on backend host |

The chat in the browser must call a **public HTTPS API** (not `127.0.0.1:8000`).

```
Browser (GitHub Pages)
        │
        │  POST https://YOUR-API.onrender.com/api/chat
        ▼
  Cloud backend (Render/Railway)
        │  GEMINI_API_KEY from host env (not GitHub)
        ▼
     Gemini + ARLIS corpus
```

---

## Step 1 — Deploy the backend (Render, free tier example)

1. Create account: [https://render.com](https://render.com)
2. **New → Web Service** → connect your GitHub repo
3. Settings:
   - **Runtime:** Docker  
   - **Dockerfile path:** `Dockerfile` (repo root)  
   - **Instance:** Free  
4. **Environment** (dashboard — not a file in Git):

   | Key | Value |
   |-----|--------|
   | `GEMINI_API_KEY` | your key from [Google AI Studio](https://aistudio.google.com/apikey) |

5. Deploy → wait until status is **Live**
6. Copy the URL, e.g. `https://wisef-rag-api.onrender.com`

### Alternative: Railway

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub  
2. Root directory / Dockerfile as above  
3. Variables → add `GEMINI_API_KEY`  
4. Generate public domain  

---

## Step 2 — Point the website at the API

Edit **`src/js/config.js`**:

```js
window.WISEF_CONFIG = {
  productionApiBase: 'https://wisef-rag-api.onrender.com',  // ← your URL, no trailing slash
  localApiBase: 'http://127.0.0.1:8000'
};
```

Commit and push. GitHub Pages will rebuild.  
**Never put the Gemini key in `config.js`.**

---

## Step 3 — CORS / HTTPS

- Backend already allows all origins (`CORS *`) for simplicity.  
- Use **https** API URL on GitHub Pages (browsers block mixed content if page is https and API is http).

---

## Step 4 — Test

1. Open live site → chat status should show **Ready** (green)  
2. Or open: `https://YOUR-API.onrender.com/api/status`  
3. Or: `https://YOUR-API.onrender.com/docs`

---

## Local development (unchanged)

```bat
start_backend.bat
start.bat
```

- Frontend: `localhost` → uses `http://127.0.0.1:8000`  
- Secret: `backend/.env` (gitignored) with `GEMINI_API_KEY=...`

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

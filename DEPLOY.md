# Deploy WISE site + AI (GitHub Pages + cloud backend)

## Recommended: one Render URL = website + AI

If you only open the Render URL and see **“WISE Social Programs RAG API”**, that is the **backend status page**, not a bug.  
With the latest Docker image, the **same URL** also serves the real website:

| URL | What you get |
|-----|----------------|
| `https://YOUR-APP.onrender.com/` | Redirects to the WISE site |
| `https://YOUR-APP.onrender.com/pages/index.html` | Full website + chat |
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

4. Deploy → open: `https://YOUR-APP.onrender.com/pages/index.html`  
5. Use **Ask us** chat (green “ready” when API is up)

**Manual deploy:** Render dashboard → **Manual Deploy → Deploy latest commit** after you push.

---

## Option B: GitHub Pages (site) + Render (API only)

1. Site: `https://YOURUSER.github.io/REPO/`  
2. API: Render Docker as above  
3. In `src/js/config.js` set:

```js
productionApiBase: 'https://YOUR-APP.onrender.com'
```

4. Push so GitHub Pages rebuilds. **Never put the API key in config.js.**

---

## Test

1. Site: `…/pages/index.html` — full design + chat  
2. API: `…/api/status` — `"status":"ready"`  
3. Docs: `…/docs`

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

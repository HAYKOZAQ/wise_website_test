# Drop MLSA / USS program PDFs here

Any `.pdf` file in this folder is extracted and indexed into the AI corpus.

## Quick import (any folder)

From the project root:

```bat
import_pdfs.bat "D:\MyMinistryPDFs"
```

Or:

```bat
python backend\bulk_import_pdfs.py "D:\MyMinistryPDFs"
python backend\reingest.py
```

Options:

```bat
python backend\bulk_import_pdfs.py "D:\pdfs" --force
python backend\bulk_import_pdfs.py --rebuild-only
```

## Full re-ingest

```bat
reingest.bat
reingest.bat --force
```

## While the API is running

```bat
REM rebuild in background + hot-reload
curl -X POST http://127.0.0.1:8000/api/admin/reingest -H "Content-Type: application/json" -d "{\"force\":false}"

REM import external folder
curl -X POST http://127.0.0.1:8000/api/admin/import-pdfs -H "Content-Type: application/json" -d "{\"source\":\"D:/MyMinistryPDFs\"}"

REM status
curl http://127.0.0.1:8000/api/admin/ingest-status
```

If `ADMIN_TOKEN` is set on the server, add header:

```text
X-Admin-Token: your-secret
```

## Scheduled refresh

**Option A — in the API process** (Render/Docker/local):

```bat
set REINGEST_INTERVAL_HOURS=24
set ADMIN_TOKEN=change-me
start_backend.bat
```

**Option B — Windows Task Scheduler:**

```powershell
.\install_scheduled_reingest.ps1
.\install_scheduled_reingest.ps1 -Hour 4 -Force
```

## Recommended sources

- [ARLIS](https://www.arlis.am/) — laws and government decisions
- [social.gov.am](https://social.gov.am/) — Ministry of Labor and Social Affairs
- [uss.social.gov.am](https://uss.social.gov.am/) — Unified Social Service

Also auto-downloaded via `backend/mlsa_pdf_catalog.json`.

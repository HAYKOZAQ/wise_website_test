@echo off
title WISE AI RAG Backend
echo ========================================================
echo   WISE Foundation — Social Programs RAG Backend
echo   ARLIS legal corpus + citizen summaries (Gemma)
echo ========================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.10+.
    pause
    exit /b 1
)

echo [1/4] Installing Python dependencies...
python -m pip install -r backend/requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [2/4] Building MLSA index (summaries + ARLIS + PDFs + web)...
python backend/scraper.py
if %errorlevel% neq 0 (
    echo [WARNING] Scraper completed with some warnings, proceeding...
)
echo       Tip: drop extra ministry PDFs into backend\pdfs\ then re-run scraper.

echo.
echo [3/4] Freeing port 8000 if occupied...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r /c:":8000 *[^ ]* *[^ ]* *LISTENING"') do (
    echo [INFO] Terminating process %%a holding port 8000...
    taskkill /f /pid %%a >nul 2>&1
)

echo.
echo [4/4] Starting FastAPI on http://127.0.0.1:8000 ...
echo.
echo NOTE: Optional local LLM via Ollama (ollama run gemma2)
echo       Or set GEMINI_API_KEY in backend/.env for Gemini cloud models.
echo       Optional: FORCE_EMBED=1 for full vector cache (slow first run).
echo       Re-ingest: in-process only by default (REINGEST_INTERVAL_HOURS=24).
echo       Do NOT also enable Windows Task Scheduler unless you set REINGEST_MODE=windows
echo         and REINGEST_INTERVAL_HOURS=0 (single schedule — no dual writers).
echo ========================================================
echo.

:: Single schedule path: in-process (disable if using install_scheduled_reingest.ps1)
if not defined REINGEST_MODE set REINGEST_MODE=inprocess
if not defined REINGEST_INTERVAL_HOURS set REINGEST_INTERVAL_HOURS=24
if /I "%REINGEST_MODE%"=="windows" set REINGEST_INTERVAL_HOURS=0
if /I "%REINGEST_MODE%"=="off" set REINGEST_INTERVAL_HOURS=0

cd backend
python -c "import json,os; os.makedirs('data',exist_ok=True); open('data/reingest_mode.json','w',encoding='utf-8').write(json.dumps({'mode':os.environ.get('REINGEST_MODE','inprocess')}))"
python main.py
pause

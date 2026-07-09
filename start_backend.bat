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
echo [2/4] Building MLSA index (citizen summaries + ARLIS acts)...
python backend/scraper.py
if %errorlevel% neq 0 (
    echo [WARNING] Scraper completed with some warnings, proceeding...
)

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
echo ========================================================
echo.

cd backend
python main.py
pause

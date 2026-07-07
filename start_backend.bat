@echo off
title WISE AI RAG Backend
echo ========================================================
echo   WISE Foundation — AI Chatbot RAG Backend (Gemma 2)
echo ========================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.10+.
    pause
    exit /b 1
)

echo [1/3] Installing Python dependencies...
python -m pip install -r backend/requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [2/3] Indexing MLSA social programs...
python backend/scraper.py
if %errorlevel% neq 0 (
    echo [WARNING] Scraper completed with some warnings, proceeding to start server...
)

echo.
echo [3/3] Starting FastAPI Uvicorn Server on http://127.0.0.1:8000...
echo.

:: Automatically release port 8000 if occupied by another instance
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r /c:":8000 *[^ ]* *[^ ]* *LISTENING"') do (
    echo [INFO] Terminating process %%a holding port 8000 to prevent socket binding error...
    taskkill /f /pid %%a >nul 2>&1
)

echo ========================================================
echo NOTE: Ensure Ollama is running locally with 'gemma2' loaded!
echo Command to run in terminal: ollama run gemma2
echo ========================================================
echo.

cd backend
python main.py
pause

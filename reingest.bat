@echo off
title WISE — Re-ingest MLSA corpus
echo ========================================================
echo   Full re-ingest: summaries + ARLIS + PDFs + web
echo ========================================================
echo.

cd /d "%~dp0"

set FORCE=
if /I "%~1"=="--force" set FORCE=--force
if /I "%~1"=="force" set FORCE=--force

python backend\reingest.py %FORCE%
set ERR=%errorlevel%

echo.
if %ERR% neq 0 (
  echo [ERROR] Re-ingest failed with code %ERR%
) else (
  echo [OK] Corpus updated.
  echo If the API is running, hot-reload with:
  echo   curl -X POST http://127.0.0.1:8000/api/admin/reload
)
pause
exit /b %ERR%

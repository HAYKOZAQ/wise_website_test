@echo off
title WISE — Bulk import MLSA PDFs
echo ========================================================
echo   Import ministry PDFs into the AI corpus
echo ========================================================
echo.
echo Usage:
echo   import_pdfs.bat
echo   import_pdfs.bat "D:\path\to\pdfs"
echo   import_pdfs.bat "D:\path\to\pdfs" --force
echo.

set "SRC=%~1"
set "EXTRA=%~2"

cd /d "%~dp0"

if "%SRC%"=="" (
  echo [INFO] No folder given — rebuilding from backend\pdfs
  python backend\bulk_import_pdfs.py --rebuild-only %EXTRA%
) else (
  echo [INFO] Importing from: %SRC%
  python backend\bulk_import_pdfs.py "%SRC%" %EXTRA%
)

if %errorlevel% neq 0 (
  echo [ERROR] Import failed.
  pause
  exit /b 1
)

echo.
echo Done. Restart backend OR call POST /api/admin/reload if server is running.
echo Prefer: python backend\reingest.py   ^(rebuild + you can reload via API^)
pause

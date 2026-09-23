@echo off
title ወልድያ EDMS Server
color 1F
echo.
echo  =====================================================
echo   ወልድያ ከተማ አስተዳደር  --  EDMS
echo   Woldiya City Administration  --  Document System
echo  =====================================================
echo.

cd /d "%~dp0"

rem Use the project's repaired virtual environment python (venv_fix)
set "PYTHON=%~dp0venv_fix\Scripts\python.exe"

echo [1/2] Applying migrations...
"%PYTHON%" manage.py migrate --run-syncdb
echo.

echo [2/2] Starting server...
echo.
echo   http://127.0.0.1:8000/
echo   http://127.0.0.1:8000/admin/
echo.
echo   Press Ctrl+C to stop.
echo  =====================================================
echo.
"%PYTHON%" manage.py runserver 0.0.0.0:8000
pause

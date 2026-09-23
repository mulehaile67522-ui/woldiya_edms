@echo off
setlocal
set "PROJECT=%~dp0"
set "PYTHON=%PROJECT%venv_fix\Scripts\python.exe"

cd /d "%PROJECT%"
"%PYTHON%" manage.py backup_data
echo.
echo Backup saved in: %PROJECT%backups
pause
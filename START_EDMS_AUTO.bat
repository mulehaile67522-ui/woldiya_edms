@echo off
chcp 65001 >nul

set PROJECT=C:\Users\muleh\OneDrive\Desktop\woldiya-emds\woldiya_edms
set PYTHON=C:\Users\muleh\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
set LOGFILE=%PROJECT%\edms_server.log

cd /d "%PROJECT%"

:: Apply migrations silently
"%PYTHON%" manage.py migrate --run-syncdb >> "%LOGFILE%" 2>&1

:: Start server in background, log output
start /B "%PYTHON%" manage.py runserver 0.0.0.0:8000 >> "%LOGFILE%" 2>&1

:: Wait 3 seconds then open browser
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8000"

exit

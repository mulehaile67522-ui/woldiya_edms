@echo off
chcp 65001 >nul

:: Kill all Django runserver processes cleanly
for /f "tokens=2" %%a in ('tasklist ^| findstr /i "python.exe"') do (
    wmic process where "ProcessId=%%a and CommandLine like '%%manage.py%%'" delete >nul 2>&1
)

:: Also kill by port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    taskkill /PID %%a /F >nul 2>&1
)

exit

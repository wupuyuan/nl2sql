@echo off

echo ===== Stop old semantic-layer process =====
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)
timeout /t 1 /nobreak >nul

echo ===== Start new semantic-layer process =====
cd /d "%~dp0"
start /B python -m uvicorn main:app --host 0.0.0.0 --port 8001

echo Done! Log file: app.log
echo Visit: http://127.0.0.1:8001
echo.
tasklist | findstr python.exe

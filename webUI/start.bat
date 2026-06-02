@echo off

echo ===== Stop old webUI process =====
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)
timeout /t 1 /nobreak >nul

echo ===== Start new webUI process =====
cd /d "%~dp0"
start /B python -m http.server 8080 --bind 127.0.0.1

echo Done! Log file: app.log
echo Visit: http://127.0.0.1:8080/index.html
echo.
tasklist | findstr python.exe

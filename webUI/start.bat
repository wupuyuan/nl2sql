@echo off

echo ===== Stop old webUI process =====
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3100 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)
timeout /t 1 /nobreak >nul

echo ===== Start Chainlit webUI =====
echo Visit: http://127.0.0.1:3100
echo Log: %~dp0app.log
cd /d "%~dp0"
python -m chainlit run chainlit_app.py --port 3100 --host 127.0.0.1 > app.log 2>&1

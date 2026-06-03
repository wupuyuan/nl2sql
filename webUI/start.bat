@echo off

echo ===== Stop old webUI process =====
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3010 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)
timeout /t 1 /nobreak >nul

echo ===== Start Chainlit webUI =====
echo Visit: http://127.0.0.1:3010
echo Log: %~dp0app.log
cd /d "%~dp0"
python -m chainlit run chainlit_app.py --port 3010 --host 0.0.0.0 > app.log 2>&1

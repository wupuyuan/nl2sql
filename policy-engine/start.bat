@echo off
cd /d "%~dp0"
echo ===== 启动 Policy Engine (ABAC 策略引擎) =====
echo 端口: 8005
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8005

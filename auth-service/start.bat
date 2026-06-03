@echo off
cd /d "%~dp0"
echo ===== 启动 Auth Service (认证鉴权服务) =====
echo 端口: 8004
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8004

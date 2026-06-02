@echo off

echo ===== Start all AI Platform services =====
echo.

echo ===== Start semantic-layer =====
call "%~dp0semantic-layer\start.bat"
timeout /t 2 /nobreak >nul
echo.

echo ===== Start metrics-engine =====
call "%~dp0metrics-engine\start.bat"
timeout /t 2 /nobreak >nul
echo.

echo ===== Start mcp-hub =====
call "%~dp0mcp-hub\start.bat"
timeout /t 2 /nobreak >nul
echo.

echo ===== Start agent-service =====
call "%~dp0agent-service\start.bat"
timeout /t 2 /nobreak >nul
echo.

echo ===== Start webUI =====
call "%~dp0webUI\start.bat"
echo.

echo ===== All services started =====
echo.
echo Service ports:
echo   semantic-layer: http://127.0.0.1:8001
echo   metrics-engine: http://127.0.0.1:8002
echo   mcp-hub:        http://127.0.0.1:8000
echo   agent-service:  http://127.0.0.1:8003
echo   webUI:          http://127.0.0.1:8080
echo.

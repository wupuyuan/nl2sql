@echo off
setlocal EnableDelayedExpansion

set "ROOT_DIR=%~dp0"
set "ROOT_DIR=%ROOT_DIR:~0,-1%"

:: Load JWT Secret from .env
if exist "%ROOT_DIR%\.env" (
    for /f "tokens=1,2 delims==" %%a in ('type "%ROOT_DIR%\.env" ^| findstr CHAINLIT_AUTH_SECRET') do (
        set "CHAINLIT_AUTH_SECRET=%%b"
    )
)
if not defined CHAINLIT_AUTH_SECRET (
    set "CHAINLIT_AUTH_SECRET=6JpOo~oQg0Bm>:Q5T-L3dy>CnU%$4CcP?GFR4_m.iUACk>.v4f_F,g8XlxgkR1ks"
)
set "PYTHON_CMD=python"

:: Check python
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] python command not found
    pause
    exit /b 1
)

echo ===== Start AI Platform services =====
echo.

:: Stop old processes
echo [1/3] Stopping old processes...
for %%p in (8004 8005 8001 8002 8000 8003 3010) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%%p ^| findstr LISTENING') do (
        taskkill /F /PID %%a >nul 2>&1
        echo   Stopped port %%p (PID %%a)
    )
)
timeout /t 2 /nobreak >nul

:: Start base services
echo.
echo [2/3] Starting base services...

cd /d "%ROOT_DIR%\auth-service"
start /B %PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 8004 > app.log 2>&1
echo   - auth-service   (8004)

cd /d "%ROOT_DIR%\policy-engine"
start /B %PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 8005 > app.log 2>&1
echo   - policy-engine  (8005)

cd /d "%ROOT_DIR%\semantic-layer"
start /B %PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 8001 > app.log 2>&1
echo   - semantic-layer (8001)

cd /d "%ROOT_DIR%\metrics-engine"
start /B %PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 8002 > app.log 2>&1
echo   - metrics-engine (8002)

echo   Waiting for base services...
timeout /t 3 /nobreak >nul

:: Start upper services
echo.
echo [3/3] Starting upper services...

cd /d "%ROOT_DIR%\mcp-hub"
start /B %PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 8000 > app.log 2>&1
echo   - mcp-hub        (8000)

cd /d "%ROOT_DIR%\agent-service"
start /B %PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 8003 > app.log 2>&1
echo   - agent-service  (8003)

echo   Waiting for upper services...
timeout /t 3 /nobreak >nul

cd /d "%ROOT_DIR%\webUI"
set "CHAINLIT_AUTH_SECRET=%CHAINLIT_AUTH_SECRET%"
start /B %PYTHON_CMD% -m chainlit run chainlit_app.py --port 3010 --host 0.0.0.0 > app.log 2>&1
echo   - webUI          (3010)

timeout /t 2 /nobreak >nul

:: Done
echo.
echo ===== All services started =====
echo.
echo Ports:
echo   auth-service   http://127.0.0.1:8004
echo   policy-engine  http://127.0.0.1:8005
echo   semantic-layer http://127.0.0.1:8001
echo   metrics-engine http://127.0.0.1:8002
echo   mcp-hub        http://127.0.0.1:8000
echo   agent-service  http://127.0.0.1:8003
echo   webUI          http://127.0.0.1:3010
echo.
echo Users:
echo   cipher_op  / 550e8400-e29b-41d4-a716-446655440000
echo   beijing    / 660e8400-e29b-41d4-a716-446655440001
echo   shanghai   / 770e8400-e29b-41d4-a716-446655440002
echo.
pause
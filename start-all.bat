@echo off
echo Starting TestFlow...
echo.

echo [1/3] Starting Backend (Port 8000)...
start cmd /k "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 2 /nobreak >nul

echo [2/3] Starting Execution Engine...
start cmd /k "cd executor && python main.py"
timeout /t 2 /nobreak >nul

echo [3/3] Starting Frontend (Port 3002)...
start cmd /k "cd frontend && npm run dev"
timeout /t 2 /nobreak >nul

echo.
echo ============================================
echo All components started successfully!
echo ============================================
echo - Backend API:    http://localhost:8000
echo - Executor:       Running as standalone app
echo - Frontend:       http://localhost:3002
echo ============================================
echo.

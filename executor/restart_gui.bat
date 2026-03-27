@echo off
REM 重启GUI服务器

echo ================================
echo   重启 Executor GUI 服务器
echo ================================

cd /d "%~dp0"

echo 关闭现有GUI服务器...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
    taskkill /PID %%a /F 2>nul
)

timeout /t 2 /nobreak >nul

echo 启动新的GUI服务器...
echo.
echo 🌐 访问地址: http://127.0.0.1:5000
echo 🔗 后端WebSocket: ws://localhost:8000/ws/executor
echo.

python -m gui.web_server

pause
@echo off
REM 启动 TestFlow 执行引擎 GUI (连接到后端WebSocket)

echo ================================
echo   TestFlow Executor GUI
echo   连接到后端WebSocket
echo ================================
echo.

cd /d "%~dp0"

echo 🌐 启动Web服务器...
echo 📱 访问地址: http://127.0.0.1:5000
echo 🔗 后端WebSocket: ws://localhost:8000/ws/executor
echo.

python -m gui.web_server

pause
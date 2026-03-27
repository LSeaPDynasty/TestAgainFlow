@echo off
REM 启动 TestFlow 执行引擎 WebSocket GUI

echo ================================
echo   TestFlow 执行引擎 WebSocket GUI
echo ================================
echo.

REM 切换到executor目录
cd /d "%~dp0"

REM 检查虚拟环境
if exist "..\..\.venv\Scripts\python.exe" (
    echo 使用虚拟环境Python...
    set PYTHON=..\..\.venv\Scripts\python.exe
) else (
    echo 使用系统Python...
    set PYTHON=python
)

REM 检查是否安装了websockets
%PYTHON% -c "import websockets" 2>nul
if errorlevel 1 (
    echo websockets未安装，正在安装依赖...
    %PYTHON% -m pip install websockets
)

echo.
echo 🌐 启动WebSocket Web服务器...
echo 📱 访问地址: http://127.0.0.1:5000
echo 🔗 后端WebSocket: ws://localhost:8000
echo 💡 按 Ctrl+C 停止服务器
echo.

REM 启动WebSocket GUI
%PYTHON% -c "import sys; sys.path.insert(0, '.'); from gui.web_server_ws import main; main()"

pause
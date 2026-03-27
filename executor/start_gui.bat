@echo off
REM 启动 TestFlow 执行引擎 Web GUI

echo ================================
echo   TestFlow 执行引擎 Web GUI
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

REM 检查是否安装了Flask
%PYTHON% -c "import flask" 2>nul
if errorlevel 1 (
    echo Flask未安装，正在安装依赖...
    %PYTHON% -m pip install flask flask-cors
)

echo.
echo 🌐 启动Web服务器...
echo 📱 访问地址: http://127.0.0.1:5000
echo 💡 按 Ctrl+C 停止服务器
echo.

REM 启动GUI
%PYTHON% start_gui.py

pause
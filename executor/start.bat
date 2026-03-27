@echo off
chcp 65001 >nul
title TestFlow 执行引擎

echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║        🤖 TestFlow Execution Engine v1.0.0                ║
echo ║                                                           ║
echo ║        Android 自动化测试执行引擎                          ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 📥 检查依赖...
pip install -q -r requirements.txt

REM 启动执行引擎
echo.
echo ▶️  启动执行引擎...
echo.
python main.py

pause

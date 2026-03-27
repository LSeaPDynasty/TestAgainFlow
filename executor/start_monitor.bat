@echo off
REM 启动执行引擎监控GUI

echo ================================
echo   TestFlow 执行引擎监控
echo ================================
echo.

cd /d "%~dp0"

echo 📱 启动监控界面...
echo 🔗 连接到执行引擎: http://127.0.0.1:5555
echo.
echo 💡 使用说明:
echo    1. 确保执行引擎正在运行 (python main.py)
echo    2. 监控界面会自动刷新显示引擎状态
echo    3. 按 Ctrl+C 关闭监控界面
echo.

python monitor.py

pause
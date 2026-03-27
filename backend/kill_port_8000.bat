@echo off
REM 关闭占用8000端口的进程并启动后端服务器

echo ================================
echo 检查占用8000端口的进程...
echo ================================

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo 发现进程 PID: %%a
    taskkill /PID %%a /F
)

echo.
echo ================================
echo 启动后端服务器...
echo ================================

python run.py

pause
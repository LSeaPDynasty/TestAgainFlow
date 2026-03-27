@echo off
REM 在端口8001上启动后端服务器

echo ================================
echo 启动后端服务器 (端口 8001)
echo ================================
echo.

set PORT=8001

python -c "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=%PORT%, reload=True)"

pause
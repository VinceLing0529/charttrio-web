@echo off
title 生命洞察前端开发服务器

echo =================================
echo 生命洞察命盘分析系统 - 前端启动
echo =================================
echo.

echo [1/3] 进入前端目录...
cd frontend

echo [2/3] 检查Node.js环境...
node --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js，请安装Node.js 16+
    pause
    exit /b 1
)

echo [3/3] 启动React开发服务器...
echo.
echo 前端应用地址: http://localhost:3000
echo.
echo 按 Ctrl+C 停止服务器
echo.

npm start

pause 
@echo off
title 生命洞察系统 - 安装依赖

echo =================================
echo 生命洞察命盘分析系统 - 依赖安装
echo =================================
echo.

echo [1/4] 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请安装Python 3.8+
    pause
    exit /b 1
)

echo [2/4] 安装后端依赖...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 错误: 后端依赖安装失败
    pause
    exit /b 1
)
cd ..

echo [3/4] 检查Node.js环境...
node --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js，请安装Node.js 16+
    pause
    exit /b 1
)

echo [4/4] 安装前端依赖...
cd frontend
npm install
if %errorlevel% neq 0 (
    echo 错误: 前端依赖安装失败
    pause
    exit /b 1
)
cd ..

echo.
echo ============================
echo 依赖安装完成！
echo ============================
echo.
echo 使用说明:
echo 1. 运行 start_backend.bat 启动后端服务器
echo 2. 运行 start_frontend.bat 启动前端开发服务器
echo 3. 打开浏览器访问 http://localhost:3000
echo.

pause 
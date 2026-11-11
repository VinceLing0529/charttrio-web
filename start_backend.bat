@echo off
title 生命洞察后端服务器

echo =================================
echo 生命洞察命盘分析系统 - 后端启动
echo =================================
echo.

echo [1/3] 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请安装Python 3.8+
    pause
    exit /b 1
)

echo [2/3] 安装依赖...
cd backend
pip install -r requirements.txt

echo [3/3] 启动FastAPI服务器...
echo.
echo 后端服务地址: http://localhost:8000
echo API文档地址: http://localhost:8000/api/docs
echo.
echo 按 Ctrl+C 停止服务器
echo.

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

pause 
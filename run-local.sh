#!/usr/bin/env bash
# LifeInsight 本地一键启动（后端 :8000 + 前端 :3000）
# 用法：bash run-local.sh   （首次会自动装依赖并构建前端）
set -e
cd "$(dirname "$0")"

# ---------- 后端 ----------
if [ ! -d backend/.venv ]; then
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install -r backend/requirements.txt
  # flatlib 锁定的 pyswisseph 2.08 在 Python 3.12 下不兼容，必须升级（见 requirements 注释）
  backend/.venv/bin/pip install -U "pyswisseph>=2.10"
fi
(cd backend/app && ../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 &)

# ---------- 前端 ----------
if [ ! -d frontend/build ]; then
  (cd frontend && npm install && REACT_APP_API_URL=http://localhost:8000 npm run build)
fi
(python3 scripts/serve-spa.py frontend/build 3000 &)

echo ""
echo "LifeInsight 已启动："
echo "  前端  http://localhost:3000"
echo "  后端  http://localhost:8000/health"
echo "停止：在本目录执行 pkill -f uvicorn; pkill -f 'serve-spa.py'"
wait

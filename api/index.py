# Vercel Serverless 入口：把 backend/app 的 FastAPI 应用暴露为函数
# Vercel 文件系统只读（除 /tmp），而后端用相对路径 data/ 存报告与 prompt，
# 因此冷启动时切换工作目录到 /tmp 并把仓库内的 prompt 模板拷过去。
import os
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

os.makedirs("/tmp/data/prompts", exist_ok=True)
os.makedirs("/tmp/data/reports", exist_ok=True)
for _src in (_ROOT / "backend" / "app" / "data" / "prompts",
             _ROOT / "backend" / "data" / "prompts"):
    if _src.is_dir():
        for _f in _src.iterdir():
            if _f.is_file():
                shutil.copy(_f, "/tmp/data/prompts/")
os.chdir("/tmp")

sys.path.insert(0, str(_ROOT / "backend" / "app"))

# 本目录也叫 api，会遮蔽后端 backend/app/api 包，先把后端的 api 包注册进 sys.modules
import importlib.util  # noqa: E402

_api_dir = _ROOT / "backend" / "app" / "api"
_spec = importlib.util.spec_from_file_location(
    "api", _api_dir / "__init__.py", submodule_search_locations=[str(_api_dir)]
)
_api_pkg = importlib.util.module_from_spec(_spec)
sys.modules["api"] = _api_pkg
_spec.loader.exec_module(_api_pkg)

from main import app  # noqa: E402,F401

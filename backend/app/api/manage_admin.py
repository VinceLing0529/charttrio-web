import os
import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/manage-admin", tags=["manage-admin"])

# 管理员凭据只从环境变量读取（见 backend/.env.example）。
# 历史教训：曾有明文凭据写死在源码并提交到公开仓库，已按泄露处理并轮换。
# 未配置环境变量时登录一律拒绝（fail closed），不提供任何默认口令。
ADMIN_USER = os.environ.get("MANAGE_ADMIN_USER", "")
ADMIN_PASS = os.environ.get("MANAGE_ADMIN_PASS", "")


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: LoginRequest):
    if not ADMIN_USER or not ADMIN_PASS:
        raise HTTPException(status_code=503, detail="管理员登录未配置（缺少环境变量）")
    user_ok = secrets.compare_digest(data.username, ADMIN_USER)
    pass_ok = secrets.compare_digest(data.password, ADMIN_PASS)
    if user_ok and pass_ok:
        return {"success": True}
    raise HTTPException(status_code=401, detail="账号或密码错误")

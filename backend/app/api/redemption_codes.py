import os
import json
import uuid
import threading
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter(prefix="/api/redemption-codes", tags=["redemption-codes"])

# ---------- 存储层 ----------
# 优先 Redis（REDIS_URL，或 REDIS_HOST/REDIS_PORT）；连不上时自动落盘到本地 JSON 文件，
# 保证无 Redis 的环境（本地演示等）兑换码功能照常可用，不再整段 500。
# 历史问题：Redis 地址曾写死 localhost:6379 且无兜底，服务不存在时五个端点全部 500。
try:
    import redis as _redis_lib
except ImportError:  # pragma: no cover
    _redis_lib = None

_redis_client = None
_redis_checked = False


def _get_redis():
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client
    _redis_checked = True
    if _redis_lib is None:
        return None
    try:
        url = os.environ.get("REDIS_URL")
        if url:
            client = _redis_lib.Redis.from_url(url, decode_responses=True, socket_connect_timeout=1, socket_timeout=2)
        else:
            client = _redis_lib.Redis(
                host=os.environ.get("REDIS_HOST", "localhost"),
                port=int(os.environ.get("REDIS_PORT", "6379")),
                db=0, decode_responses=True, socket_connect_timeout=1, socket_timeout=2,
            )
        client.ping()
        _redis_client = client
    except Exception as e:
        print(f"兑换码存储：Redis 不可用（{e}），改用本地文件存储")
        _redis_client = None
    return _redis_client


_FILE_PATH = Path(__file__).resolve().parents[1] / "data" / "redemption_codes.json"
_FILE_LOCK = threading.Lock()


def _file_load() -> dict:
    try:
        return json.loads(_FILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _file_save(data: dict) -> None:
    _FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _FILE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def _store_get(code: str) -> Optional[dict]:
    client = _get_redis()
    if client is not None:
        raw = client.get(f"redemption_code:{code}")
        return json.loads(raw) if raw else None
    with _FILE_LOCK:
        return _file_load().get(code)


def _store_set_many(items: list) -> None:
    """批量写入：文件模式只做一次读+写，避免逐个写入的 O(n^2) 整表重写。"""
    if not items:
        return
    client = _get_redis()
    if client is not None:
        for code, info in items:
            ttl = max(60, int((datetime.fromisoformat(info["expires_at"]) - datetime.now()).total_seconds()))
            client.setex(f"redemption_code:{code}", ttl, json.dumps(info))
        return
    with _FILE_LOCK:
        data = _file_load()
        for code, info in items:
            data[code] = info
        _file_save(data)


def _store_set(code: str, info: dict) -> None:
    client = _get_redis()
    if client is not None:
        ttl = max(60, int((datetime.fromisoformat(info["expires_at"]) - datetime.now()).total_seconds()))
        client.setex(f"redemption_code:{code}", ttl, json.dumps(info))
        return
    with _FILE_LOCK:
        data = _file_load()
        data[code] = info
        _file_save(data)


def _store_delete(code: str) -> bool:
    client = _get_redis()
    if client is not None:
        return client.delete(f"redemption_code:{code}") > 0
    with _FILE_LOCK:
        data = _file_load()
        if code in data:
            del data[code]
            _file_save(data)
            return True
        return False


def _store_all() -> List[dict]:
    client = _get_redis()
    if client is not None:
        out = []
        for key in client.scan_iter(match="redemption_code:*"):
            raw = client.get(key)
            if raw:
                out.append(json.loads(raw))
        return out
    with _FILE_LOCK:
        return list(_file_load().values())

class CodeRequest(BaseModel):
    code: str

class CodeResponse(BaseModel):
    code: str
    is_valid: bool
    used_at: Optional[str] = None
    created_at: Optional[str] = None

class GenerateCodeRequest(BaseModel):
    # quantity 必须设界：无上限时一次生成上万个码会把文件存储拖成 O(n^2) 并堵死事件循环（实测 10000 个卡死全站约 5 分钟）
    quantity: int = Field(1, ge=1, le=100)
    expires_in_days: int = Field(30, ge=1, le=3650)

class CodeInfo(BaseModel):
    code: str
    is_used: bool
    created_at: str
    used_at: Optional[str] = None
    expires_at: str

# 生成兑换码
def generate_code() -> str:
    """生成唯一的兑换码"""
    return f"LIFE{uuid.uuid4().hex[:8].upper()}"

# 验证兑换码
@router.post("/verify", response_model=CodeResponse)
async def verify_code(request: CodeRequest):
    """验证兑换码是否有效"""
    try:
        code = request.code.upper().strip()

        code_info = _store_get(code)

        if not code_info:
            raise HTTPException(status_code=404, detail="兑换码不存在")
        
        # 检查是否已过期
        expires_at = datetime.fromisoformat(code_info['expires_at'])
        if datetime.now() > expires_at:
            raise HTTPException(status_code=400, detail="兑换码已过期")
        
        # 检查是否已使用
        if code_info['is_used']:
            raise HTTPException(status_code=400, detail="兑换码已被使用")
        
        # 标记为已使用
        code_info['is_used'] = True
        code_info['used_at'] = datetime.now().isoformat()
        _store_set(code, code_info)
        
        return CodeResponse(
            code=code,
            is_valid=True,
            used_at=code_info['used_at'],
            created_at=code_info['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"验证兑换码错误: {e}")
        raise HTTPException(status_code=500, detail="验证失败")

# 生成新兑换码
@router.post("/generate")
async def generate_codes(request: GenerateCodeRequest):
    """生成新的兑换码"""
    try:
        codes = []
        items = []
        expires_at = datetime.now() + timedelta(days=request.expires_in_days)

        for _ in range(request.quantity):
            code = generate_code()
            code_info = {
                'code': code,
                'is_used': False,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat()
            }
            items.append((code, code_info))
            codes.append(code)

        _store_set_many(items)
        
        return {
            "success": True,
            "codes": codes,
            "quantity": request.quantity,
            "expires_at": expires_at.isoformat()
        }
        
    except Exception as e:
        print(f"生成兑换码错误: {e}")
        raise HTTPException(status_code=500, detail="生成失败")

# 获取兑换码列表
@router.get("/list", response_model=List[CodeInfo])
async def list_codes():
    """获取所有兑换码列表"""
    try:
        codes = [CodeInfo(**info) for info in _store_all()]
        
        # 按创建时间排序
        codes.sort(key=lambda x: x.created_at, reverse=True)
        return codes
        
    except Exception as e:
        print(f"获取兑换码列表错误: {e}")
        raise HTTPException(status_code=500, detail="获取失败")

# 删除兑换码
@router.delete("/{code}")
async def delete_code(code: str):
    """删除指定兑换码"""
    try:
        code = code.upper().strip()

        if not _store_delete(code):
            raise HTTPException(status_code=404, detail="兑换码不存在")

        return {"success": True, "message": "兑换码已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"删除兑换码错误: {e}")
        raise HTTPException(status_code=500, detail="删除失败")

# 获取兑换码统计信息
@router.get("/stats")
async def get_stats():
    """获取兑换码统计信息"""
    try:
        total_codes = 0
        used_codes = 0
        valid_codes = 0

        for code_info in _store_all():
            total_codes += 1
            if code_info['is_used']:
                used_codes += 1
            else:
                # 检查是否过期
                expires_at = datetime.fromisoformat(code_info['expires_at'])
                if datetime.now() <= expires_at:
                    valid_codes += 1
        
        return {
            "total_codes": total_codes,
            "used_codes": used_codes,
            "valid_codes": valid_codes,
            "usage_rate": round(used_codes / total_codes * 100, 2) if total_codes > 0 else 0
        }
        
    except Exception as e:
        print(f"获取统计信息错误: {e}")
        raise HTTPException(status_code=500, detail="获取失败") 
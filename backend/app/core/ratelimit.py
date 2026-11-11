"""极简内存限速（防 AI 接口被刷爆 token）。

按 (作用域, IP) 做滑动窗口计数，用作 FastAPI 路由依赖。
单机/单进程部署够用；多副本时各副本独立计数，上量后应换 Redis 计数。

IP 取值：优先 X-Forwarded-For 第一跳（生产经反代/Vercel 时的真实客户端），
否则用直连地址。
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_buckets: dict = defaultdict(deque)


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(scope: str, max_calls: int, window_seconds: int = 60):
    """返回一个 FastAPI 依赖：窗口内同一 IP 超过 max_calls 次 → 429。"""

    async def _dep(request: Request):
        key = (scope, _client_ip(request))
        now = time.monotonic()
        q = _buckets[key]
        while q and now - q[0] > window_seconds:
            q.popleft()
        if len(q) >= max_calls:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
        q.append(now)

    return _dep

# -*- coding: utf-8 -*-
"""
在线支付（Stripe Checkout）——路径 C：美国 LLC + Stripe 跨境。

设计：站点不自建账户体系，Stripe 付款成功后自动发放一枚兑换码
（与现有兑换码体系同一存储），成功页凭 session_id 取码。
这正是 Metis 的"付完自动开通"在本架构下的最小实现：
支付只是兑换码的自动售货机，报告解锁逻辑零改动。

未配置 STRIPE_SECRET_KEY 时全部端点返回未启用状态，不影响现有卖码链路。
密钥只从环境变量读，禁止入库、入仓、入日志。
"""
import json
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from core.ratelimit import rate_limit

router = APIRouter(prefix="/api/payments", tags=["payments"])

_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "payments.json"
_LOCK = threading.Lock()

PRICE_FEN = int(os.environ.get("STRIPE_PRICE_FEN", "2490"))  # $24.90
CURRENCY = os.environ.get("STRIPE_CURRENCY", "usd")
PRODUCT_NAME = "ChartTrio Full Birth Chart Report (4 modules)"


def _secret_key() -> str:
    return os.environ.get("STRIPE_SECRET_KEY", "").strip()


def _webhook_secret() -> str:
    return os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()


def _public_base() -> str:
    return os.environ.get("PUBLIC_BASE_URL", "http://localhost:3000").rstrip("/")


def stripe_enabled() -> bool:
    return bool(_secret_key())


def _stripe():
    import stripe  # 延迟导入：未装/未启用时不影响其余端点
    stripe.api_key = _secret_key()
    return stripe


def _load() -> dict:
    try:
        return json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    _DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _DATA_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(_DATA_PATH)


def _issue_code_for_session(session_id: str) -> Optional[str]:
    """为已付款 session 发放兑换码（幂等：已发过直接返回原码）。"""
    from api.redemption_codes import generate_code, _store_set
    with _LOCK:
        data = _load()
        rec = data.get(session_id) or {}
        if rec.get("code"):
            return rec["code"]
        code = generate_code()
        _store_set(code, {
            "code": code,
            "is_used": False,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=365)).isoformat(),
            "source": "stripe",
            "session_id": session_id,
        })
        rec.update({"code": code, "status": "paid",
                    "paid_at": datetime.now().isoformat()})
        data[session_id] = rec
        _save(data)
        return code


@router.get("/config")
async def payments_config():
    return {"stripe_enabled": stripe_enabled(), "price_fen": PRICE_FEN,
            "currency": CURRENCY}


class CheckoutResponse(BaseModel):
    url: str
    session_id: str


@router.post("/stripe/checkout", response_model=CheckoutResponse,
             dependencies=[Depends(rate_limit("stripe-checkout", 10, 60))])
async def create_checkout():
    if not stripe_enabled():
        raise HTTPException(status_code=503, detail="在线支付未启用")
    stripe = _stripe()
    base = _public_base()
    params = dict(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": CURRENCY,
                "unit_amount": PRICE_FEN,
                "product_data": {"name": PRODUCT_NAME},
            },
            "quantity": 1,
        }],
        success_url=f"{base}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base}/?pay=cancelled",
        metadata={"product": "ai_report_unlock"},
    )
    # 支付方式由 Stripe Dashboard 设置决定（卡 + 支付宝已启用）；
    # 新版 Stripe API 已禁止在建单时传 payment_method_types。
    session = stripe.checkout.Session.create(**params)
    with _LOCK:
        data = _load()
        data[session.id] = {"status": "created",
                            "created_at": datetime.now().isoformat(),
                            "amount_fen": PRICE_FEN}
        _save(data)
    return CheckoutResponse(url=session.url, session_id=session.id)


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    if not stripe_enabled() or not _webhook_secret():
        raise HTTPException(status_code=503, detail="webhook 未启用")
    stripe = _stripe()
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, _webhook_secret())
    except Exception:
        raise HTTPException(status_code=400, detail="签名验证失败")
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        if not isinstance(session, dict):
            session = session.to_dict()  # 新版 stripe-python 返回对象而非 dict
        if session.get("payment_status") == "paid":
            _issue_code_for_session(session["id"])
    return {"received": True}


@router.get("/stripe/session/{session_id}")
async def get_session(session_id: str):
    """成功页取码：先看本地记录；webhook 未达时向 Stripe 核验后补发。"""
    with _LOCK:
        rec = _load().get(session_id) or {}
    if rec.get("code"):
        return {"status": "paid", "code": rec["code"]}
    if not stripe_enabled():
        return {"status": rec.get("status", "unknown"), "code": None}
    stripe = _stripe()
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception:
        raise HTTPException(status_code=404, detail="会话不存在")
    if not isinstance(session, dict):
        session = session.to_dict()  # 新版 stripe-python 返回对象而非 dict
    if session.get("payment_status") == "paid":
        code = _issue_code_for_session(session_id)
        return {"status": "paid", "code": code}
    return {"status": session.get("payment_status") or "unpaid", "code": None}

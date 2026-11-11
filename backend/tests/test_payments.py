# -*- coding: utf-8 -*-
"""Stripe 支付端点测试（SDK 全 mock，不触网、不烧真 key）。"""
import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def payments_env(monkeypatch, tmp_path):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_fake")
    import api.payments as pay
    importlib.reload(pay)
    monkeypatch.setattr(pay, "_DATA_PATH", tmp_path / "payments.json")
    app = FastAPI()
    app.include_router(pay.router)
    return pay, TestClient(app)


class _FakeSession(dict):
    @property
    def id(self):
        return self["id"]

    @property
    def url(self):
        return self["url"]


class _FakeStripe:
    def __init__(self):
        self.created = []
        outer = self

        class _SessionNS:
            @staticmethod
            def create(**kwargs):
                outer.created.append(kwargs)
                return _FakeSession(id="cs_test_123",
                                    url="https://checkout.stripe.com/pay/cs_test_123")

            @staticmethod
            def retrieve(sid):
                return {"id": sid, "payment_status": "paid"}

        class _WebhookNS:
            @staticmethod
            def construct_event(payload, sig, secret):
                return {"type": "checkout.session.completed",
                        "data": {"object": {"id": "cs_test_123",
                                            "payment_status": "paid"}}}

        self.checkout = type("C", (), {"Session": _SessionNS})
        self.Webhook = _WebhookNS


def test_config_enabled(payments_env):
    _, client = payments_env
    r = client.get("/api/payments/config")
    assert r.status_code == 200 and r.json()["stripe_enabled"] is True
    assert r.json()["price_fen"] == 2490
    assert r.json()["currency"] == "usd"


def test_checkout_creates_session(payments_env, monkeypatch):
    pay, client = payments_env
    fake = _FakeStripe()
    monkeypatch.setattr(pay, "_stripe", lambda: fake)
    r = client.post("/api/payments/stripe/checkout")
    assert r.status_code == 200
    assert r.json()["session_id"] == "cs_test_123"
    # 新版 Stripe API 禁止建单时传 payment_method_types（方式由 Dashboard 设置决定）
    assert "payment_method_types" not in fake.created[0]


def test_webhook_issues_code_idempotently(payments_env, monkeypatch):
    pay, client = payments_env
    fake = _FakeStripe()
    monkeypatch.setattr(pay, "_stripe", lambda: fake)
    r = client.post("/api/payments/stripe/webhook", content=b"{}",
                    headers={"stripe-signature": "t=1,v1=x"})
    assert r.status_code == 200
    code1 = pay._issue_code_for_session("cs_test_123")
    code2 = pay._issue_code_for_session("cs_test_123")
    assert code1 and code1 == code2 and code1.startswith("LIFE")
    r2 = client.get("/api/payments/stripe/session/cs_test_123")
    assert r2.json()["code"] == code1


def test_disabled_without_key(monkeypatch, tmp_path):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    import api.payments as pay
    importlib.reload(pay)
    monkeypatch.setattr(pay, "_DATA_PATH", tmp_path / "payments.json")
    app = FastAPI()
    app.include_router(pay.router)
    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/api/payments/config").json()["stripe_enabled"] is False
    assert client.post("/api/payments/stripe/checkout").status_code == 503

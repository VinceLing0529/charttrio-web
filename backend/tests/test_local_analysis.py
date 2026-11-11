# -*- coding: utf-8 -*-
"""Tests for api/analysis.py local rule engine and /local-analysis wrapper.

Rules under test: conclusions must be derived from the supplied chart
(never canned text), missing data must degrade to an explicit
insufficient-data answer instead of crashing or inventing, and garbage
types must not raise.
"""
import asyncio

import pytest
from fastapi import HTTPException

from api.analysis import AnalysisRequest, _perform_local_analysis, local_analysis

TYPES = ["personality", "career", "wealth", "relationship", "health",
         "comprehensive"]


def run(req):
    return asyncio.run(local_analysis(req))


def test_ling_comprehensive_derives_from_chart(ling_chart):
    r = _perform_local_analysis(ling_chart, "comprehensive")
    assert r["confidence"] == "medium"
    assert "All three charts, one reading" in r["summary"]
    assert any("Bing Fire" in b for b in r["basis"])
    assert any("Body Palace: Spouse Palace" in b for b in r["basis"])
    assert any("紫府同宫" in b for b in r["basis"])
    assert any("紫府同宫" in p for p in r["key_points"])
    assert any("Body Palace sits in the Spouse Palace" in p for p in r["key_points"])
    assert r["suggestions"]
    assert all(isinstance(p, str) and p for p in r["key_points"])


def test_ling_engine_chart_matches_hand_built(ling_chart_engine, ling_chart):
    # The hand-built fixture must agree with the live engine on the facts
    # the tests assert, so fixture drift is caught here, not silently.
    r_eng = _perform_local_analysis(ling_chart_engine, "comprehensive")
    r_fix = _perform_local_analysis(ling_chart, "comprehensive")
    assert any("Bing Fire" in b for b in r_eng["basis"])
    assert any("紫府同宫" in p for p in r_eng["key_points"])
    assert any("Body Palace sits in the Spouse Palace" in p for p in r_eng["key_points"])
    eng_pats = {b for b in r_eng["basis"] if b.startswith("Patterns:")}
    fix_pats = {b for b in r_fix["basis"] if b.startswith("Patterns:")}
    assert eng_pats == fix_pats


@pytest.mark.parametrize("atype", TYPES)
def test_ling_all_analysis_types_return_shape(ling_chart, atype):
    r = _perform_local_analysis(ling_chart, atype)
    assert r["summary"]
    assert r["key_points"]
    assert r["suggestions"]
    assert r["confidence"] in ("medium", "low")


def test_ling_relationship_uses_male_spouse_star(ling_chart):
    r = _perform_local_analysis(ling_chart, "relationship")
    # 配偶星落在要点里 (summary 只写日支与夫妻宫主星)
    assert any("财星" in p for p in r["key_points"])


def test_synth_chart_derives_different_conclusions(synth_chart):
    r = _perform_local_analysis(synth_chart, "comprehensive")
    assert any("Geng Metal" in b for b in r["basis"])
    assert any("杀破狼" in b for b in r["basis"])
    assert any("杀破狼" in p for p in r["key_points"])
    assert r["summary"]


def test_synth_relationship_uses_female_spouse_star(synth_chart):
    r = _perform_local_analysis(synth_chart, "relationship")
    assert any("官杀" in p for p in r["key_points"])


@pytest.mark.parametrize("atype", TYPES)
def test_synth_all_types_no_crash(synth_chart, atype):
    r = _perform_local_analysis(synth_chart, atype)
    assert r["summary"] and r["key_points"]


def test_analysis_is_deterministic(ling_chart):
    a = _perform_local_analysis(ling_chart, "comprehensive")
    b = _perform_local_analysis(ling_chart, "comprehensive")
    assert a == b


def test_empty_chart_reports_insufficient_data():
    r = _perform_local_analysis({}, "comprehensive")
    assert r["confidence"] == "low"
    assert "Chart data is missing" in r["summary"]
    assert r["key_points"] == []


@pytest.mark.parametrize("bad_chart", [
    None, "not-a-dict", ["bazi"],
    {"bazi": "not-a-dict", "ziwei": ["palaces"], "vedic": 42},
    {"bazi": {"five_elements_count": "nonsense", "ten_gods": None}},
])
def test_garbage_chart_data_never_raises(bad_chart):
    r = _perform_local_analysis(bad_chart, "comprehensive")
    assert isinstance(r, dict)
    assert r["summary"]


def test_partial_bazi_only_chart_still_derives(ling_chart):
    partial = {"input": ling_chart["input"], "bazi": ling_chart["bazi"]}
    r = _perform_local_analysis(partial, "personality")
    assert "Bing Fire" in r["summary"]
    assert r["confidence"] == "medium"


def test_endpoint_success_shape(ling_chart):
    resp = run(AnalysisRequest(chart_data=ling_chart,
                               analysis_type="personality"))
    assert resp["success"] is True
    assert resp["message"] == "Quick reading complete"
    assert resp["data"]["summary"]
    assert resp["data"]["key_points"]


def test_endpoint_rejects_unknown_type(ling_chart):
    with pytest.raises(HTTPException) as exc:
        run(AnalysisRequest(chart_data=ling_chart, analysis_type="nope"))
    assert exc.value.status_code == 400

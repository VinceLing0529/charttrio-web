# -*- coding: utf-8 -*-
"""Tests for core/shensha.py (tables from ShousenZHANG/chinese-fortune, MIT).

Hand-computed expectations are spelled out in conftest.py; the Ling case
is cross-checked against the 13 hits recorded for his chart in the
overnight log (包1)."""
import pytest

from core.shensha import GLOSS, detect_shensha
from conftest import LING_BAZI, SYNTH_BAZI


def test_ling_bazi_thirteen_hits():
    hits = detect_shensha(LING_BAZI)
    assert len(hits) == len(set(hits)) == 13  # 去重
    assert set(hits) == {
        "福星贵人", "学堂", "词馆", "天厨贵人", "飞刃", "红艳煞",
        "劫煞", "灾煞", "驿马", "将星", "亡神", "孤辰", "天德合",
    }
    # No 空亡: 丙子属甲子旬 (空戌亥), 四柱地支寅巳子巳无戌亥.
    assert "空亡" not in hits
    # No 魁罡: only 庚辰/庚戌/壬辰/戊戌 days qualify.
    assert "魁罡" not in hits


def test_synth_bazi_hand_computed_hits():
    hits = detect_shensha(SYNTH_BAZI)
    assert set(hits) == {
        "太极贵人", "福星贵人", "国印贵人", "天厨贵人", "灾煞",
        "驿马", "华盖", "将星", "寡宿", "魁罡", "三奇贵人",
    }
    assert len(hits) == 11


def test_synth_bazi_kuigang_and_sanqi_spelled_out():
    # 庚辰日 itself is a 魁罡 day; stems 戊/甲/庚 form the 甲戊庚 trio.
    hits = detect_shensha(SYNTH_BAZI)
    assert "魁罡" in hits
    assert "三奇贵人" in hits
    # 庚辰属甲戌旬 (空申酉), 四柱地支午寅辰子无申酉.
    assert "空亡" not in hits


def test_every_detected_name_has_a_gloss():
    for bazi in (LING_BAZI, SYNTH_BAZI):
        for name in detect_shensha(bazi):
            assert name in GLOSS and GLOSS[name], name


def test_kongwang_positive_case():
    # 甲子日属甲子旬 (空戌亥); 时支戌命中空亡.
    hits = detect_shensha({
        "year_pillar": "甲子", "month_pillar": "丙寅",
        "day_pillar": "甲子", "hour_pillar": "戊戌", "day_master": "甲",
    })
    assert "空亡" in hits


def test_missing_or_partial_input_never_crashes():
    assert detect_shensha({}) == []
    assert detect_shensha({"year_pillar": "戊寅"}) == []
    # Day pillar too short to parse => treated as absent.
    assert detect_shensha({"day_pillar": "丙"}) == []
    # Only a day pillar: still runs, and the obvious day-stem hits land.
    hits = detect_shensha({"day_pillar": "丙子"})
    assert "福星贵人" in hits  # 丙见子
    assert "天厨贵人" in hits  # 丙见子
    assert isinstance(hits, list)


def test_no_day_master_falls_back_to_day_stem():
    bazi = {k: v for k, v in LING_BAZI.items() if k != "day_master"}
    assert detect_shensha(bazi) == detect_shensha(LING_BAZI)

# -*- coding: utf-8 -*-
"""Tests for core/ziwei_patterns.py (port of Renhuai123/ziwei-doushu patterns.ts).

判定口径以 patterns.ts 原版为准：四星全格与三星会互斥、破格单独列出、
三方四正 = 命/财/官 + 对宫（迁移）。"""
import copy

import pytest

from core.ziwei_patterns import detect
from conftest import (
    LING_FOUR_TRANS, LING_PALACES, SYNTH_FOUR_TRANS_B, SYNTH_PALACES_A,
    SYNTH_PALACES_B, palace,
)


def names(patterns):
    return [p["name"] for p in patterns]


def by_name(patterns, name):
    for p in patterns:
        if p["name"] == name:
            return p
    raise AssertionError(f"pattern {name!r} not in {names(patterns)}")


# ---------------------------------------------------------------- Ling
def test_ling_chart_known_patterns():
    """Ling's verified chart: the five patterns recorded for his chart."""
    pats = detect(LING_PALACES, LING_FOUR_TRANS)
    found = names(pats)
    for expected in ("紫府同宫", "廉贞天相格", "天机化忌入命",
                     "机月同梁三星会", "昌曲同会"):
        assert expected in found, found
    # 三星会, not the four-star full pattern: 太阴 sits in 福德卯,
    # outside 命/财/官/迁, so the fourth star never joins sanfang.
    assert "机月同梁" not in found


def test_ling_lianxiang_breaking_recorded():
    pat = by_name(detect(LING_PALACES, LING_FOUR_TRANS), "廉贞天相格")
    assert pat["level"] == "caution"
    assert pat["breaking"] == ["廉相宫坐擎羊"]


def test_ling_zifu_not_in_ming_is_good_not_excellent():
    pat = by_name(detect(LING_PALACES, LING_FOUR_TRANS), "紫府同宫")
    assert pat["level"] == "good"  # 紫府在父母宫, 会照减力


def test_ling_tianji_huaji_in_ming():
    pat = by_name(detect(LING_PALACES, LING_FOUR_TRANS), "天机化忌入命")
    assert pat["level"] == "caution"
    assert "天机" in pat["desc"]


# ------------------------------------------------------------- synthetic
def test_synth_a_shapolang_and_huotan():
    pats = detect(SYNTH_PALACES_A, {"禄": "贪狼", "权": "太阴", "科": "右弼", "忌": "天机"})
    found = names(pats)
    assert "杀破狼" in found
    assert "火贪格" in found
    assert "马头带箭" in found
    assert by_name(pats, "马头带箭")["level"] == "good"  # 七杀会照, 成威
    # No accidental 机月同梁 family: none of those four stars is present.
    assert not [n for n in found if "机月同梁" in n]


def test_synth_b_junchen_riyue_shuanglu():
    pats = detect(SYNTH_PALACES_B, SYNTH_FOUR_TRANS_B)
    found = names(pats)
    assert "君臣庆会" in found
    assert by_name(pats, "君臣庆会")["level"] == "excellent"
    assert "日月同宫" in found
    assert "双禄朝垣" in found
    assert "紫微入命" in found  # 紫微独坐命宫, 辅弼会照 => excellent
    assert by_name(pats, "紫微入命")["level"] == "excellent"


def test_four_star_jiyue_full_pattern_excludes_three_star():
    """Adding 太阴 into sanfang upgrades 三星会 to the four-star pattern."""
    palaces = copy.deepcopy(LING_PALACES)
    palaces["财帛"]["minor_stars"].append("太阴")  # 财帛酉在三方内
    found = names(detect(palaces, LING_FOUR_TRANS))
    assert "机月同梁" in found
    assert "机月同梁三星会" not in found


def test_zifu_breaking_and_in_ming_levels():
    # 紫府同宫 + 空劫同坐 => breaking, level drops to good even in 命宫.
    palaces = {
        "命宫": palace("丑", [("紫微", "旺", ""), ("天府", "庙", "")],
                        minors=["地空", "地劫"]),
    }
    pat = by_name(detect(palaces, {}), "紫府同宫")
    assert pat["level"] == "good"
    assert "紫府宫坐空劫" in pat["breaking"]
    # 紫府同宫 clean and in 命宫 => excellent.
    palaces["命宫"]["minor_stars"] = []
    pat = by_name(detect(palaces, {}), "紫府同宫")
    assert pat["level"] == "excellent"
    assert pat["breaking"] == []


def test_shuanglu_breaking_with_kongjie_in_ming():
    palaces = {
        "命宫": palace("丑", [("武曲", "庙", "禄")], minors=["地空"]),
        "财帛": palace("巳", [], minors=["禄存"]),
    }
    pat = by_name(detect(palaces, {}), "双禄朝垣")
    assert pat["breaking"] == ["命坐空劫（双禄遇空，财来财去）"]


# ------------------------------------------------------------- robustness
@pytest.mark.parametrize("bad", [{}, {"命宫": {"major_stars": []}},
                                 {"命宫": "not-a-dict"}, None])
def test_empty_or_malformed_input_returns_no_patterns(bad):
    assert detect(bad, {}) == []
    assert detect(bad, None) == []


def test_palace_without_branch_is_ignored():
    palaces = {"命宫": palace("", [("紫微", "旺", "")])}
    assert detect(palaces, {}) == []  # 命宫无地支 => 无法定三方


def test_output_shape():
    pats = detect(LING_PALACES, LING_FOUR_TRANS)
    assert pats
    for p in pats:
        assert set(p) == {"name", "level", "desc", "breaking",
                          "name_en", "desc_en", "breaking_en"}
        assert p["level"] in ("excellent", "good", "neutral", "caution")
        assert isinstance(p["desc"], str) and p["desc"]
        assert isinstance(p["breaking"], list)

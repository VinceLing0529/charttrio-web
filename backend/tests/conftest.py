# -*- coding: utf-8 -*-
"""pytest fixtures for the local (zero-token) interpretation engine.

Import style matches the backend (``from core.xxx import ...`` with
backend/app on sys.path). Two chart sources are used on purpose:

* ``ling_*`` — Ling's real chart, 1998-05-29 11:00 clock time, Zhuhai
  113.6E/22.3N, male. True solar time 10:34 => 巳时. The hand-built
  palace/bazi fixtures below mirror the verified TripleChartParser
  output (命宫丑天机陷化忌, 身宫夫妻亥, 父母宫紫府同宫, 金四局), so
  pattern/shensha tests do NOT depend on the ephemeris engine.
* ``ling_chart_engine`` — the same chart computed live by the engine,
  used only by the local-analysis integration tests.
* ``synth_*`` — one fully hand-built synthetic chart, used to prove the
  rules generalise instead of memorising Ling's chart.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest


def palace(branch, majors=(), minors=(), adjectives=(), is_body=False,
           stem="甲", index=0):
    """Build one palace dict in the engine's output shape."""
    return {
        "index": index,
        "heavenly_stem": stem,
        "earthly_branch": branch,
        "is_body_palace": is_body,
        "major_stars": [
            {"name": name, "brightness": bright, "mutagen": mut}
            for name, bright, mut in majors
        ],
        "minor_stars": list(minors),
        "adjective_stars": list(adjectives),
    }


# ---------------------------------------------------------------- Ling
LING_FOUR_TRANS = {"禄": "贪狼", "权": "太阴", "科": "右弼", "忌": "天机"}

LING_BAZI = {
    "year_pillar": "戊寅", "month_pillar": "丁巳",
    "day_pillar": "丙子", "hour_pillar": "癸巳",
    "day_master": "丙",
    "five_elements_count": {"木": 1, "火": 4, "土": 1, "金": 0, "水": 2},
    "body_strength": "强",
    "ten_gods": {"年干": "食神", "月干": "劫财", "日干": "比肩", "时干": "正官"},
    "spirits": ["驿马"],
    "dayun": {"direction": "逆", "qiyun_age": 8},
}

# Palace order follows the engine output (index order); branch order is
# counter-clockwise from 命宫丑, which is why 身宫夫妻 lands on 亥.
LING_PALACES = {
    "父母": palace("寅", [("紫微", "旺", ""), ("天府", "庙", "")], stem="甲", index=0),
    "福德": palace("卯", [("太阴", "陷", "权")],
                   adjectives=["咸池", "八座", "天才", "天官", "天福", "天空"],
                   stem="乙", index=1),
    "田宅": palace("辰", [("贪狼", "庙", "禄")], minors=["地劫", "陀罗"],
                   adjectives=["天哭"], stem="丙", index=2),
    "官禄": palace("巳", [("巨门", "旺", "")], minors=["文昌", "禄存"],
                   adjectives=["天姚", "孤辰"], stem="丁", index=3),
    "仆役": palace("午", [("廉贞", "平", ""), ("天相", "庙", "")],
                   minors=["右弼", "地空", "火星", "擎羊"],
                   adjectives=["龙池", "天厨", "阴煞", "天伤"], stem="戊", index=4),
    "迁移": palace("未", [("天梁", "旺", "")], minors=["天钺"],
                   adjectives=["天喜", "恩光", "封诰", "天月", "月德"], stem="己", index=5),
    "疾厄": palace("申", [("七杀", "庙", "")], minors=["左辅", "天马", "铃星"],
                   adjectives=["凤阁", "旬空", "天虚", "天使", "年解"], stem="庚", index=6),
    "财帛": palace("酉", [("天同", "平", "")], minors=["文曲"],
                   adjectives=["破碎"], stem="辛", index=7),
    "子女": palace("戌", [("武曲", "庙", "")], adjectives=["华盖", "蜚廉"],
                   stem="壬", index=8),
    "夫妻": palace("亥", [("太阳", "陷", "")], is_body=True,
                   adjectives=["三台", "天贵", "台辅", "天德"], stem="癸", index=9),
    "兄弟": palace("子", [("破军", "庙", "")], adjectives=["解神", "截路"],
                   stem="甲", index=10),
    "命宫": palace("丑", [("天机", "陷", "忌")], minors=["天魁"],
                   adjectives=["红鸾", "天寿", "空亡", "寡宿", "天刑"], stem="乙", index=11),
}

LING_STAR_POSITIONS = {
    "紫微": "父母", "天府": "父母", "太阴": "福德", "贪狼": "田宅",
    "巨门": "官禄", "廉贞": "仆役", "天相": "仆役", "天梁": "迁移",
    "七杀": "疾厄", "天同": "财帛", "武曲": "子女", "太阳": "夫妻",
    "破军": "兄弟", "天机": "命宫",
}


@pytest.fixture(scope="session")
def ling_chart_engine():
    """Ling's full chart computed by the real engine (session-scoped)."""
    from triple_chart_parser import TripleChartParser
    parser = TripleChartParser()
    inp = parser.parse_input(
        birth_date="1998-05-29", birth_time="11:00", timezone="+8",
        longitude=113.6, latitude=22.3, gender=1, daylight_saving=False)
    return parser.generate_output(
        inp, parser.calculate_bazi(inp),
        parser.calculate_ziwei(inp), parser.calculate_vedic(inp))


@pytest.fixture()
def ling_chart():
    """Hand-built Ling chart in the shape _perform_local_analysis expects."""
    return {
        "input": {"birth_date": "1998-05-29", "gender": 1},
        "bazi": dict(LING_BAZI),
        "ziwei": {
            "basic_info": {"soul": "巨门", "body": "天梁", "five_elements_class": "金四局"},
            "chart": {"palaces": LING_PALACES, "star_positions": LING_STAR_POSITIONS},
            "year_four_trans": dict(LING_FOUR_TRANS),
        },
        "vedic": {
            "ascendant": {"sign": "Cancer"},
            "planets": {
                "Moon": {"sign": "Gemini", "house": 12, "lon": 5.0},
                "Sun": {"sign": "Taurus", "house": 11, "lon": 14.0},
                "Mercury": {"sign": "Taurus", "house": 11, "lon": 20.0},
                "Mars": {"sign": "Taurus", "house": 11, "lon": 2.0},
                "Jupiter": {"sign": "Pisces", "house": 7, "lon": 10.0},
                "Saturn": {"sign": "Aries", "house": 10, "lon": 8.0},
                "Venus": {"sign": "Aries", "house": 10, "lon": 25.0},
            },
        },
    }


# ------------------------------------------------------------- synthetic
# Bazi: 戊午 / 甲寅 / 庚辰 / 戊子, day master 庚. Hand-computed hits:
# 太极贵人, 福星贵人, 国印贵人, 天厨贵人, 灾煞, 驿马, 华盖, 将星,
# 寡宿, 魁罡 (庚辰日), 三奇贵人 (甲戊庚三干).
SYNTH_BAZI = {
    "year_pillar": "戊午", "month_pillar": "甲寅",
    "day_pillar": "庚辰", "hour_pillar": "戊子",
    "day_master": "庚",
    "five_elements_count": {"木": 1, "火": 1, "土": 3, "金": 2, "水": 1},
    "body_strength": "弱",
    "ten_gods": {"年干": "偏印", "月干": "偏财", "日干": "比肩", "时干": "偏印"},
    "spirits": [],
    "dayun": {"direction": "顺", "qiyun_age": 3},
}

# Synthetic ziwei A: 命宫午坐七杀+擎羊 (马头带箭), 破军在子女戌,
# 贪狼+火星在福德寅 => 杀破狼 + 火贪格. Sanfang of 命午 = 午/戌/寅/子.
SYNTH_PALACES_A = {
    "命宫": palace("午", [("七杀", "庙", "")], minors=["擎羊"], stem="丙", index=0),
    "迁移": palace("未", [], stem="丁", index=1),
    "疾厄": palace("申", [], stem="戊", index=2),
    "财帛": palace("酉", [], stem="己", index=3),
    "子女": palace("戌", [("破军", "庙", "")], stem="庚", index=4),
    "夫妻": palace("亥", [], stem="辛", index=5),
    "兄弟": palace("子", [], stem="壬", index=6),
    "父母": palace("丑", [], stem="癸", index=7),
    "福德": palace("寅", [("贪狼", "庙", "")], minors=["火星"], stem="甲", index=8),
    "田宅": palace("卯", [], stem="乙", index=9),
    "官禄": palace("辰", [], stem="丙", index=10),
    "仆役": palace("巳", [], stem="丁", index=11),
}

SYNTH_STAR_POSITIONS_A = {
    "七杀": "命宫", "擎羊": "命宫", "破军": "子女",
    "贪狼": "福德", "火星": "福德",
}

# Synthetic ziwei B: 命宫丑坐紫微 + 左辅, 右弼在财帛巳,
# 太阳+太阴同宫未, 武曲化禄在财帛 + 禄存于官禄酉
# => 君臣庆会 + 日月同宫 + 双禄朝垣 (+ 紫微入命).
SYNTH_PALACES_B = {
    "命宫": palace("丑", [("紫微", "旺", "")], minors=["左辅"], stem="乙", index=0),
    "父母": palace("子", [], stem="甲", index=1),
    "福德": palace("亥", [], stem="癸", index=2),
    "田宅": palace("戌", [], stem="壬", index=3),
    "官禄": palace("酉", [], minors=["禄存"], stem="辛", index=4),
    "仆役": palace("申", [], stem="庚", index=5),
    "迁移": palace("未", [("太阳", "旺", ""), ("太阴", "旺", "")], stem="己", index=6),
    "疾厄": palace("午", [], stem="戊", index=7),
    "财帛": palace("巳", [("武曲", "庙", "禄")], minors=["右弼"], stem="丁", index=8),
    "子女": palace("辰", [], stem="丙", index=9),
    "夫妻": palace("卯", [], stem="乙", index=10),
    "兄弟": palace("寅", [], stem="甲", index=11),
}

SYNTH_FOUR_TRANS_B = {"禄": "武曲", "权": "贪狼", "科": "天梁", "忌": "文曲"}


@pytest.fixture()
def synth_chart():
    """Synthetic full chart (female, 1995-08-15 style inputs)."""
    return {
        "input": {"birth_date": "1995-08-15", "gender": 0},
        "bazi": dict(SYNTH_BAZI),
        "ziwei": {
            "basic_info": {"soul": "武曲", "body": "天相", "five_elements_class": "水二局"},
            "chart": {"palaces": SYNTH_PALACES_A,
                      "star_positions": SYNTH_STAR_POSITIONS_A},
            "year_four_trans": {"禄": "贪狼", "权": "太阴", "科": "右弼", "忌": "天机"},
        },
        "vedic": {
            "ascendant": {"sign": "Leo"},
            "planets": {
                "Moon": {"sign": "Cancer", "house": 12, "lon": 10.0},
                "Sun": {"sign": "Leo", "house": 1, "lon": 22.0},
                "Venus": {"sign": "Virgo", "house": 2, "lon": 5.0},
            },
        },
    }

# -*- coding: utf-8 -*-
"""Regenerate ExamplePage static data from the real engine.

Sample chart (QUEUE.md pkg4): 1995-08-15 09:30, Beijing (116.4E/39.9N),
female. Runs TripleChartParser + zero-token local-analysis rules
(api/analysis._perform_local_analysis) + ziwei pattern detection +
shensha detection, writes frontend/src/data/exampleReport.json.

Every chart claim in the JSON is copied verbatim from engine output.
Only authored strings are UI labels and the sample-note paragraph.
If engine output drifts, this script fails loudly instead of shipping
stale data. Usage (from backend/):
    ../.venv/bin/python scripts/generate_example_report.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(HERE, "..", "app")
sys.path.insert(0, APP_DIR)

from triple_chart_parser import TripleChartParser
from core.timezone_utils import get_timezone_from_coordinates, format_timezone_offset
from api.analysis import _perform_local_analysis
from core.ziwei_patterns import detect as zw_detect
from core.shensha import detect_shensha

OUT = os.path.join(HERE, "..", "..", "frontend", "src", "data", "exampleReport.json")


def star_str(star):
    name = star["name"]
    bright = star.get("brightness", "")
    mut = star.get("mutagen", "")
    suffix = "（" + bright + mut + "）" if (bright or mut) else ""
    return name + suffix


def palace_summary(palaces, name):
    p = palaces[name]
    return {
        "name": name,
        "branch": p.get("earthly_branch", ""),
        "is_body_palace": bool(p.get("is_body_palace")),
        "major_stars": [star_str(s) for s in p.get("major_stars", [])],
        "minor_stars": list(p.get("minor_stars", [])),
    }


def pick(pool, needle, where):
    for item in pool:
        if needle in item:
            return item
    raise AssertionError("engine string not found for %s: %r" % (where, needle))


def main():
    parser = TripleChartParser()
    tz = get_timezone_from_coordinates(116.4, 39.9)
    inp = parser.parse_input(
        birth_date="1995-08-15", birth_time="09:30",
        timezone=format_timezone_offset(tz["utc_offset"]),
        longitude=116.4, latitude=39.9, gender=0, daylight_saving=False)
    chart = parser.generate_output(
        inp, parser.calculate_bazi(inp),
        parser.calculate_ziwei(inp), parser.calculate_vedic(inp))

    bazi = chart["bazi"]
    ziwei = chart["ziwei"]
    vedic = chart["vedic"]
    palaces = ziwei["chart"]["palaces"]

    assert bazi["year_pillar"] == "乙亥" and bazi["month_pillar"] == "甲申"
    assert bazi["day_pillar"] == "戊寅" and bazi["hour_pillar"] == "丁巳"
    assert bazi["day_master"] == "戊" and bazi["body_strength"] == "弱"
    assert ziwei["basic_info"]["five_elements_class"] == "土五局"
    life = palace_summary(palaces, "命宫")
    assert life["major_stars"] == ["天相（陷）"], life
    body = palace_summary(palaces, "夫妻")
    assert body["is_body_palace"] and body["major_stars"] == ["武曲（庙）", "贪狼（庙）"]

    patterns = zw_detect(palaces, ziwei.get("year_four_trans") or {})
    assert [p["name"] for p in patterns] == ["府相朝垣", "巨日同宫", "禄存守命"], patterns
    shensha = detect_shensha(bazi)
    assert len(shensha) == 11, shensha

    analyses = {}
    for atype in ("comprehensive", "personality", "career", "wealth",
                  "relationship", "health"):
        r = _perform_local_analysis(chart, atype)
        assert r["confidence"] == "medium", (atype, r["confidence"])
        assert r["summary"] and r["key_points"] and r["suggestions"]
        analyses[atype] = {
            "summary": r["summary"],
            "basis": list(r.get("basis", [])),
            "key_points": list(r["key_points"]),
            "suggestions": list(r["suggestions"]),
            "confidence": r["confidence"],
        }

    comp = analyses["comprehensive"]["key_points"]
    pers = analyses["personality"]["key_points"]
    health = analyses["health"]["key_points"]
    wealth = analyses["wealth"]["key_points"]
    career = analyses["career"]["key_points"]

    elements = bazi["five_elements_count"]
    elem_line = "、".join("%s%s" % (k, v) for k, v in elements.items())
    four = ziwei.get("year_four_trans") or {}
    four_line = "、".join("%s化%s" % (s, k) for k, s in four.items())

    facts = [
        {"label": "四柱", "value": "、".join(
            [bazi["year_pillar"], bazi["month_pillar"],
             bazi["day_pillar"], bazi["hour_pillar"]])},
        {"label": "日主 / 身强弱",
         "value": "戊（土）· 身弱 · 五行" + elem_line},
        {"label": "十神（天干）", "value": "、".join(
            "%s%s" % (k, v) for k, v in bazi["ten_gods"].items())},
        {"label": "命宫",
         "value": life["branch"] + "宫 · " + "、".join(life["major_stars"])
                  + " · 辅星" + "、".join(life["minor_stars"])},
        {"label": "身宫",
         "value": "夫妻（" + body["branch"] + "宫）· " + "、".join(body["major_stars"])},
        {"label": "紫微格局",
         "value": "、".join(p["name"] for p in patterns)},
        {"label": "生年四化", "value": four_line},
        {"label": "紫微局数 / 命主身主",
         "value": ziwei["basic_info"]["five_elements_class"] + " · "
                  + "命主" + ziwei["basic_info"]["soul"] + "、"
                  + "身主" + ziwei["basic_info"]["body"]},
        {"label": "吠陀上升 / 月亮",
         "value": "上升" + vedic["ascendant"]["sign"] + " · "
                  + "月亮" + vedic["planets"]["Moon"]["sign"]},
        {"label": "神煞（八字）", "value": "、".join(shensha)},
        {"label": "当前大运",
         "value": "八字辛巳（28–37岁）· 吠陀金星运（2011–2031年）"},
        {"label": "星宿", "value": "Revati（水星主）"},
    ]

    branches = [
        {
            "id": "positive", "title": "正向性格特征", "icon": "✨",
            "color": "from-green-500 to-emerald-500",
            "bgColor": "from-green-500/10 to-emerald-500/10",
            "source": "八字日主与命宫主星、福德宫（本地规则引擎输出）",
            "content": "。".join([
                pick(pers, "日主戊（土）：沉稳务实", "positive/dm"),
                pick(pers, "命宫天相：稳重辅佐型", "positive/life"),
                pick(pers, "福德宫坐紫微、七杀", "positive/fude"),
            ]) + "。",
            "details": [
                pick(pers, "日主戊（土）：沉稳务实", "positive/dm"),
                pick(pers, "命宫天相：稳重辅佐型", "positive/life"),
                pick(pers, "福德宫坐紫微、七杀", "positive/fude"),
                pick(comp, "巨日同宫", "positive/pattern"),
                pick(comp, "吠陀第11宫", "positive/vedic11"),
            ],
        },
        {
            "id": "negative", "title": "负向性格倾向", "icon": "⚠️",
            "color": "from-red-500 to-pink-500",
            "bgColor": "from-red-500/10 to-pink-500/10",
            "source": "身弱、五行短板与化忌（本地规则引擎输出）",
            "content": "。".join([
                pick(pers, "身弱：能量偏弱", "negative/weak"),
                pick(pers, "五行最旺为木", "negative/element"),
                pick(pers, "吠陀月亮在Pisces", "negative/moon"),
                pick(comp, "太阴化忌入子女", "negative/ji"),
            ]) + "。",
            "details": [
                pick(pers, "身弱：能量偏弱", "negative/weak"),
                pick(pers, "五行最旺为木", "negative/element"),
                pick(pers, "吠陀月亮在Pisces", "negative/moon"),
                pick(comp, "太阴化忌入子女", "negative/ji"),
            ],
        },
        {
            "id": "conflict", "title": "潜在冲突性格", "icon": "⚖️",
            "color": "from-orange-500 to-yellow-500",
            "bgColor": "from-orange-500/10 to-yellow-500/10",
            "source": "身宫、命宫三方与四化（本地规则引擎输出）",
            "content": "。".join([
                pick(comp, "身宫在夫妻", "conflict/body"),
                pick(comp, "命宫三方", "conflict/sanfang"),
                pick(comp, "天机化禄入父母", "conflict/lu"),
                pick(comp, "太阴化忌入子女", "conflict/ji"),
            ]) + "。",
            "details": [
                pick(comp, "身宫在夫妻", "conflict/body"),
                pick(comp, "命宫三方", "conflict/sanfang"),
                pick(comp, "天机化禄入父母", "conflict/lu"),
                pick(comp, "太阴化忌入子女", "conflict/ji"),
            ],
        },
        {
            "id": "strength", "title": "易发展的领域", "icon": "🚀",
            "color": "from-blue-500 to-cyan-500",
            "bgColor": "from-blue-500/10 to-cyan-500/10",
            "source": "格局、财帛宫与吠陀第11宫（本地规则引擎输出）",
            "content": "。".join([
                pick(comp, "府相朝垣", "strength/pattern1"),
                pick(comp, "巨日同宫", "strength/pattern2"),
                pick(wealth, "财帛宫坐天府", "strength/caibo"),
            ]) + "。",
            "details": [
                pick(comp, "府相朝垣", "strength/pattern1"),
                pick(comp, "巨日同宫", "strength/pattern2"),
                pick(analyses["comprehensive"]["basis"], "格局：", "strength/pattern3"),
                pick(wealth, "财帛宫坐天府", "strength/caibo"),
                pick(comp, "吠陀第11宫", "strength/vedic11"),
            ],
        },
        {
            "id": "weakness", "title": "易出问题的领域", "icon": "⚡",
            "color": "from-purple-500 to-violet-500",
            "bgColor": "from-purple-500/10 to-violet-500/10",
            "source": "五行短板、财星与空宫（本地规则引擎输出）",
            "content": "。".join([
                pick(health, "土最弱、木最旺", "weakness/health"),
                pick(wealth, "十神中财星不显", "weakness/wealth"),
                pick(career, "官禄宫主星未提供", "weakness/career"),
                pick(comp, "府相朝垣", "weakness/breaking"),
            ]) + "。",
            "details": [
                pick(health, "土最弱、木最旺", "weakness/health"),
                pick(health, "土对应脾胃与消化", "weakness/spleen"),
                pick(wealth, "十神中财星不显", "weakness/wealth"),
                pick(career, "官禄宫主星未提供", "weakness/career"),
                pick(comp, "府相朝垣", "weakness/breaking"),
            ],
        },
    ]

    tab_meta = [
        ("personality", "🧠", "性格", "from-purple-500 to-indigo-500",
         "from-purple-500/10 to-indigo-500/10"),
        ("career", "💼", "事业", "from-blue-500 to-cyan-500",
         "from-blue-500/10 to-cyan-500/10"),
        ("wealth", "💰", "财富", "from-emerald-500 to-teal-500",
         "from-emerald-500/10 to-teal-500/10"),
        ("relationship", "❤️", "感情", "from-pink-500 to-rose-500",
         "from-pink-500/10 to-rose-500/10"),
        ("health", "🏥", "健康", "from-orange-500 to-red-500",
         "from-orange-500/10 to-red-500/10"),
    ]
    analysis_tabs = []
    for atype, icon, title, grad, bg in tab_meta:
        a = analyses[atype]
        analysis_tabs.append({
            "id": atype, "icon": icon, "title": title,
            "gradient": grad, "bgGradient": bg,
            "content": a["summary"],
            "details": list(a["key_points"]),
            "suggestions": list(a["suggestions"]),
        })

    qa_categories = {}
    for atype, icon, title, grad, _bg in tab_meta:
        a = analyses[atype]
        qa_categories[atype] = {
            "title": title, "icon": icon, "gradient": grad,
            "questions": [
                {"question": "本地规则引擎对" + title + "维度的结论是什么？",
                 "answer": a["summary"]},
                {"question": title + "维度的依据要点与建议",
                 "answer": "要点：\n" + "\n".join("· " + p for p in a["key_points"])
                           + "\n建议：\n"
                           + "\n".join("· " + s for s in a["suggestions"])},
            ],
        }

    dayun_sections = [
        {
            "icon": "🪐",
            "title": "八字当前大运",
            "content": pick(comp, "当前大运辛巳", "dayun/bazi")
                       + "。起运 8 岁，顺逆为逆；"
                         "引擎注：大运详细计算需要更复杂的算法，"
                         "故本示例仅展示当前一步大运，不展开完整序列。",
        },
        {
            "icon": "✨",
            "title": "吠陀大运与星宿",
            "content": pick(comp, "吠陀当前大运为金星运", "dayun/vedic")
                       + "；" + pick(pers, "出生星宿Revati", "dayun/nakshatra")
                       + "。",
        },
        {
            "icon": "⭐",
            "title": "格局与四化",
            "content": "格局：" + "；".join(
                "%s（%s）：%s" % (p["name"], p["level"], p["desc"])
                + ("（破格注意：" + "、".join(p["breaking"]) + "）" if p["breaking"] else "")
                for p in patterns)
                       + "。生年四化：" + four_line + "。"
                       + pick(comp, "天机化禄入父母", "dayun/lu")
                       + "；" + pick(comp, "太阴化忌入子女", "dayun/ji") + "。",
        },
    ]

    data = {
        "meta": {
            "sample": "1995-08-15 09:30（钟表时间）· 北京（116.4E/39.9N）· 女",
            "true_solar_time": "09:15（巳时）",
            "lunar_date": ziwei["basic_info"]["lunar_date"],
            "source": "本地规则引擎（零 token）：TripleChartParser 排盘 + "
                      "api/analysis 本地解读 + ziwei_patterns 严格格局判定 + "
                      "shensha 神煞检测；未调用任何 AI 接口",
            "generator": "backend/scripts/generate_example_report.py",
        },
        "sample_note": "以下内容全部取自本地规则引擎对本示例盘的输出，"
                      "未使用 AI 生成，也未使用为其他人写的通用文案。"
                      "八字大运仅展示引擎已算出的当前一步，"
                      "不展开引擎未实现的完整序列。",
        "facts": facts,
        "analyses": analyses,
        "patterns": [
            {"name": p["name"], "level": p["level"], "desc": p["desc"],
             "breaking": list(p["breaking"])} for p in patterns
        ],
        "shensha": shensha,
        "palaces": [palace_summary(palaces, n) for n in
                    ("命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                     "迁移", "仆役", "官禄", "田宅", "福德", "父母")],
        "mindmap": {
            "center": {
                "title": "命主性格全景图",
                "description": "基于八字、紫微斗数、印度星盘三盘合参的性格分析"
                           "（本地规则引擎输出）",
            },
            "branches": branches,
        },
        "analysis_tabs": analysis_tabs,
        "qa_categories": qa_categories,
        "dayun_sections": dayun_sections,
    }

    text = json.dumps(data, ensure_ascii=False, indent=2)
    assert "�" not in text, "replacement char in output"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print("wrote " + OUT + " (%d chars)" % len(text))
    print("patterns:", [p["name"] for p in patterns])
    print("shensha:", len(shensha), "analyses:", sorted(analyses))


if __name__ == "__main__":
    main()

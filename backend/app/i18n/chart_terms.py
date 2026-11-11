#!/usr/bin/env python3
"""
ChartTrio (en-tree) 英译层：把 /api/charts/calculate 的原始盘面数据（中文值）
翻译成前端可直接渲染的英文展示树（响应里的 data.display）。

设计决定（与中文站 clean-tree 的区别）：
- en-tree 是独立的英文站部署，calculate 的页面消费者只有英文前端，因此
  本站默认全量英译，不设 lang 参数（调用方漏传参就会漏译，更脆）。
- 原始 data 一字不改：盘面中文值是报告 prompt 组装（ai_report）与免费速读
  规则引擎（api/analysis.py 按中文值查表）的输入契约，原地改值会把它们打坏。
  英译只出现在新增的 display 树里；前端渲染只读 display，悬浮词条的 key
  仍取原始中文值（display 每个条目都带 key 字段回指原文），与
  frontend/src/data/glossary.js 的键（'stem:甲' 等）严格对齐。
- 展示文案风格与 glossary.js 标题对齐：拼音 + 字形括注，如 'Jia (甲)'；
  宫位对齐 glossary 的 'Life Palace (命宫)' 式译名。
- 查不到映射的字符串原样返回（宁可漏译被巡检抓到，不可编造译名）；
  验证脚本会对 display 树做 CJK 残留扫描（括注内的字形除外）。
"""

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------- 基础表

STEM_PINYIN = {
    "甲": "Jia", "乙": "Yi", "丙": "Bing", "丁": "Ding", "戊": "Wu",
    "己": "Ji", "庚": "Geng", "辛": "Xin", "壬": "Ren", "癸": "Gui",
}
BRANCH_PINYIN = {
    "子": "Zi", "丑": "Chou", "寅": "Yin", "卯": "Mao", "辰": "Chen", "巳": "Si",
    "午": "Wu", "未": "Wei", "申": "Shen", "酉": "You", "戌": "Xu", "亥": "Hai",
}
ELEMENT_EN = {"金": "Metal", "木": "Wood", "水": "Water", "火": "Fire", "土": "Earth"}

# 十神：与 glossary.js 的 tengod 标题一致（生活化命名，非术语直译）
TEN_GOD_EN = {
    "比肩": "The Companion", "劫财": "The Rival",
    "食神": "The Easy Talent", "伤官": "The Sharp Edge",
    "偏财": "Windfall Wealth", "正财": "Steady Wealth",
    "七杀": "The Pressure Star", "正官": "The Authority Star",
    "偏印": "The Unusual Muse", "正印": "The Mentor Star",
}

STRENGTH_EN = {"强": "Strong", "弱": "Weak"}
DIRECTION_EN = {"顺": "Forward", "逆": "Reverse"}
GENDER_EN = {"男": "Male", "女": "Female"}

PILLAR_LABEL_EN = {"年柱": "Year Pillar", "月柱": "Month Pillar",
                   "日柱": "Day Pillar", "时柱": "Hour Pillar"}
STEM_POSITION_EN = {"年干": "Year Stem", "月干": "Month Stem",
                    "日干": "Day Stem", "时干": "Hour Stem"}

# 纳音 30 种（六十甲子两组共用）：通俗直译 + 字形括注
NAYIN_EN = {
    "海中金": "Gold in the Sea", "炉中火": "Fire in the Furnace",
    "大林木": "Great Forest Wood", "路旁土": "Earth by the Roadside",
    "剑锋金": "Sword-Edge Metal", "山头火": "Mountain-Top Fire",
    "涧下水": "Water in the Ravine", "城头土": "Earth on the City Wall",
    "白腊金": "White Wax Metal", "白蜡金": "White Wax Metal",
    "沙中土": "Earth in the Sand", "泉中水": "Spring Water",
    "霹雳火": "Thunderbolt Fire", "松柏木": "Pine-and-Cypress Wood",
    "长流水": "Long-Flowing Water", "屋上土": "Earth on the Rooftop",
    "山下火": "Fire at the Mountain Foot", "沙中金": "Metal in the Sand",
    "平地木": "Level-Ground Wood", "杨柳木": "Willow Wood",
    "桑柘木": "Mulberry Wood", "覆灯火": "Lamp Fire",
    "天河水": "Milky Way Water", "大溪水": "Great Stream Water",
    "天上火": "Heavenly Fire", "大海水": "Great Sea Water",
    "大驿土": "Great Post-Road Earth", "石榴木": "Pomegranate Wood",
    "金箔金": "Gold Foil", "钗钏金": "Hairpin-and-Bracelet Metal",
    "壁上土": "Earth on the Wall", "砂中金": "Gold in the Gravel",
}

# 十二长生（星运）
GROWTH_STATE_EN = {
    "长生": "Growth", "沐浴": "Bathing", "冠带": "Capping", "临官": "Taking Office",
    "帝旺": "Peak", "衰": "Decline", "病": "Sickness", "死": "Death",
    "墓": "The Tomb", "绝": "Exhaustion", "胎": "Conception", "养": "Nurturing",
}

VOID_EN = {"空亡": "Void", "无": "—"}

# 神煞：排盘引擎（triple_chart_parser.calculate_spirits）实际产出 5 个；
# 另附 core/shensha.py 的完整名单作兜底覆盖（其他路径若引用同一展示层不漏译）
SPIRIT_EN = {
    "天乙贵人": "Noble Helper", "桃花": "Peach Blossom",
    "驿马": "Travel Horse", "华盖": "The Canopy",
    "无特殊神煞": "No special markers",
    "文昌贵人": "Scholar Noble", "太极贵人": "Tai Chi Noble",
    "福星贵人": "Fortune Noble", "国印贵人": "State Seal Noble",
    "学堂": "The Academy", "词馆": "The Institute",
    "天德贵人": "Heavenly Virtue Noble", "月德贵人": "Lunar Virtue Noble",
    "天德合": "Heavenly Virtue Union", "月德合": "Lunar Virtue Union",
    "天厨贵人": "Heavenly Kitchen Noble", "红鸾": "Red Phoenix",
    "天喜": "Heavenly Joy", "金舆": "Golden Carriage",
    "羊刃": "The Blade", "飞刃": "Flying Blade",
    "劫煞": "Robbery Sha", "灾煞": "Disaster Sha",
    "桃花咸池": "Peach Blossom", "红艳煞": "Red Charm",
    "孤辰": "Lone Star", "寡宿": "Widow Star", "将星": "General Star",
    "亡神": "Lost Spirit", "大耗": "Great Waste", "小耗": "Small Waste",
}

# 固定说明串（引擎里的占位/说明文案）
NOTE_EN = {
    "大运详细计算需要更复杂的算法":
        "A full luck-cycle timeline needs the extended calculation, "
        "so only the cycle direction and starting age are shown for now.",
}

# enhanced_features 里的开发说明串（前端目前未渲染，仅备展示层完整性）
VEDIC_FEATURES_EN = [
    "Sidereal chart on the Lahiri ayanamsa",
    "Complete planet and axis-point data",
    "Precise house calculations",
    "Outer planets and special points supported",
]
VEDIC_NOTE_EN = "Built on the full Vedic engine, using the birth time you entered"
ZIWEI_FEATURES_EN = {
    "core": "Core chart data: 5 views ready",
    "fortune": "Cycles and timing: 4 views ready",
    "relations": "Palace relations: 4 views ready",
    "total": "13 core views, fully implemented",
}

_PLACEHOLDERS = {"暂未实现", "未实现", "未知", ""}


def _pair(en: str, zh: str) -> str:
    """'Jia (甲)' 式展示串：英文名 + 字形括注，与 glossary 标题风格一致。"""
    return f"{en} ({zh})"


def _named(table: Dict[str, str], raw: Any) -> Dict[str, Any]:
    """{text, key} 条目：text 为英译展示串，key 为原始中文值（供词条映射）。"""
    raw = raw if isinstance(raw, str) else ""
    en = table.get(raw)
    return {"text": _pair(en, raw) if en else raw, "key": raw}


def stem_item(raw: Any) -> Dict[str, Any]:
    return _named(STEM_PINYIN, raw)


def branch_item(raw: Any) -> Dict[str, Any]:
    return _named(BRANCH_PINYIN, raw)


def element_item(raw: Any) -> Dict[str, Any]:
    return _named(ELEMENT_EN, raw)


def tengod_item(raw: Any) -> Dict[str, Any]:
    return _named(TEN_GOD_EN, raw)


def star_item(raw: Any) -> Dict[str, Any]:
    """紫微星曜（主星/辅星/杂曜统一查表）。"""
    raw = raw if isinstance(raw, str) else ""
    en = STAR_EN.get(raw) or ADJECTIVE_STAR_EN.get(raw)
    return {"text": _pair(en, raw) if en else raw, "key": raw}


def palace_item(raw: Any) -> Dict[str, Any]:
    raw = raw if isinstance(raw, str) else ""
    en = PALACE_EN.get(raw)
    if en:
        glyph = raw if raw.endswith("宫") else raw + "宫"
        return {"text": _pair(en, glyph), "key": raw}
    return {"text": raw, "key": raw}


def sihua_item(raw: Any) -> Dict[str, Any]:
    return _named(SIHUA_EN, raw)


def pillar_pair(raw: Any) -> str:
    """干支对 → 'Yi Hai (乙亥)'。"""
    raw = raw if isinstance(raw, str) else ""
    if len(raw) == 2 and raw[0] in STEM_PINYIN and raw[1] in BRANCH_PINYIN:
        return _pair(f"{STEM_PINYIN[raw[0]]} {BRANCH_PINYIN[raw[1]]}", raw)
    return raw


def nayin_text(raw: Any) -> str:
    raw = raw if isinstance(raw, str) else ""
    en = NAYIN_EN.get(raw)
    return _pair(en, raw) if en else raw


def five_elements_class_text(raw: Any) -> str:
    """格局：'土五局' → 'Earth-5 Structure (土五局)'（白话式，不直译「局」）。"""
    raw = raw if isinstance(raw, str) else ""
    nums = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}
    if len(raw) == 3 and raw[0] in ELEMENT_EN and raw[1] in nums and raw[2] == "局":
        return _pair(f"{ELEMENT_EN[raw[0]]}-{nums[raw[1]]} Structure", raw)
    return raw

# ---------------------------------------------------------------- 紫微表

# 十四主星 + 十四辅星：英文名与 glossary.js 的 star 标题严格一致
STAR_EN = {
    "紫微": "Zi Wei", "天机": "Tian Ji", "太阳": "Tai Yang", "武曲": "Wu Qu",
    "天同": "Tian Tong", "廉贞": "Lian Zhen", "天府": "Tian Fu", "太阴": "Tai Yin",
    "贪狼": "Tan Lang", "巨门": "Ju Men", "天相": "Tian Xiang", "天梁": "Tian Liang",
    "七杀": "Qi Sha", "破军": "Po Jun",
    "文昌": "Wen Chang", "文曲": "Wen Qu", "左辅": "Zuo Fu", "右弼": "You Bi",
    "天魁": "Tian Kui", "天钺": "Tian Yue", "禄存": "Lu Cun", "天马": "Tian Ma",
    "火星": "Huo Xing", "铃星": "Ling Xing", "擎羊": "Qing Yang", "陀罗": "Tuo Luo",
    "地空": "Di Kong", "地劫": "Di Jie",
}

# 杂曜 38（540 盘抽样全集；拼音 + 字形括注，与主星风格统一）
ADJECTIVE_STAR_EN = {
    "三台": "San Tai", "八座": "Ba Zuo", "凤阁": "Feng Ge", "华盖": "Hua Gai",
    "台辅": "Tai Fu", "咸池": "Xian Chi", "天伤": "Tian Shang", "天使": "Tian Shi",
    "天刑": "Tian Xing", "天厨": "Tian Chu", "天哭": "Tian Ku", "天喜": "Tian Xi",
    "天姚": "Tian Yao", "天官": "Tian Guan", "天寿": "Tian Shou", "天巫": "Tian Wu",
    "天德": "Tian De", "天才": "Tian Cai", "天月": "Tian Yue", "天福": "Tian Fu",
    "天空": "Tian Kong", "天虚": "Tian Xu", "天贵": "Tian Gui", "孤辰": "Gu Chen",
    "寡宿": "Gua Su", "封诰": "Feng Gao", "年解": "Nian Jie", "恩光": "En Guang",
    "截路": "Jie Lu", "旬空": "Xun Kong", "月德": "Yue De", "破碎": "Po Sui",
    "空亡": "Kong Wang", "红鸾": "Hong Luan", "蜚廉": "Fei Lian", "解神": "Jie Shen",
    "阴煞": "Yin Sha", "龙池": "Long Chi",
}

# 十二宫：与 glossary.js 的 palace 标题一致（括注补全「宫」字）
PALACE_EN = {
    "命宫": "Life Palace", "兄弟": "Siblings Palace", "父母": "Parents Palace",
    "福德": "Fortune Palace", "田宅": "Property Palace", "官禄": "Career Palace",
    "仆役": "Friends Palace", "迁移": "Travel Palace", "疾厄": "Health Palace",
    "财帛": "Wealth Palace", "子女": "Children Palace", "夫妻": "Spouse Palace",
}

SIHUA_EN = {"禄": "Lu", "权": "Quan", "科": "Ke", "忌": "Ji"}

BRIGHTNESS_EN = {
    "庙": "Peak", "旺": "Strong", "得": "Favorable", "利": "Helpful",
    "平": "Neutral", "不": "Dim", "陷": "Fallen",
}

# ---------------------------------------------------------------- 农历

_CN_DIGIT = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
             "六": 6, "七": 7, "八": 8, "九": 9, "〇": 0, "零": 0}
_LUNAR_RE = None  # 延迟编译，避免模块级 re 依赖顺序问题


def _cn_int(s: str) -> Optional[int]:
    """中文小数字：七/十/十一/二十/二十三/廿三 等。"""
    if not s:
        return None
    if s in _CN_DIGIT:
        return _CN_DIGIT[s]
    if s[0] == "十":
        rest = s[1:]
        return 10 + (_CN_DIGIT.get(rest, 0) if rest else 0)
    if len(s) >= 2 and s[1] == "十":
        tail = s[2:]
        return _CN_DIGIT.get(s[0], 0) * 10 + (_CN_DIGIT.get(tail, 0) if tail else 0)
    if s[0] == "廿" and len(s) == 2:
        return 20 + _CN_DIGIT.get(s[1], 0)
    return None


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def lunar_date_en(raw: Any) -> Optional[str]:
    """'一九九五年七月二十' → '20th day of the 7th lunar month, 1995'。

    处理正/冬/腊月别名、闰月、初/廿日写法；解析不出返回 None（前端显示占位）。
    """
    global _LUNAR_RE
    if not isinstance(raw, str) or not raw or raw in _PLACEHOLDERS:
        return None
    import re
    if _LUNAR_RE is None:
        _LUNAR_RE = re.compile(r"^([一二三四五六七八九〇零]{4})年(闰)?(.+?)月(.+)$")
    m = _LUNAR_RE.match(raw.strip())
    if not m:
        return None
    year = "".join(str(_CN_DIGIT.get(c, "")) for c in m.group(1))
    if len(year) != 4:
        return None
    leap = bool(m.group(2))
    month_tok, day_tok = m.group(3), m.group(4)
    if month_tok == "正":
        month = 1
    elif month_tok == "冬":
        month = 11
    elif month_tok == "腊":
        month = 12
    else:
        month = _cn_int(month_tok)
    if day_tok.startswith("初"):
        day = _cn_int(day_tok[1:])
    elif day_tok.startswith("廿"):
        day = 20 + (_CN_DIGIT.get(day_tok[1:], 0) if len(day_tok) > 1 else 0)
    elif day_tok.startswith("二十"):
        day = 20 + (_CN_DIGIT.get(day_tok[2:], 0) if len(day_tok) > 2 else 0)
    elif day_tok.startswith("三十"):
        day = 30
    else:
        day = _cn_int(day_tok)
    if not month or not day:
        return None
    leap_txt = "leap " if leap else ""
    return f"{_ordinal(day)} day of the {leap_txt}{_ordinal(month)} lunar month, {year}"

# ---------------------------------------------------------------- 展示树

def _seg(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []


def _brightness_text(raw: Any) -> Optional[str]:
    raw = raw if isinstance(raw, str) else ""
    if not raw:
        return None
    en = BRIGHTNESS_EN.get(raw)
    return _pair(en, raw) if en else raw


def _mutagen_item(raw: Any) -> Optional[Dict[str, Any]]:
    raw = raw if isinstance(raw, str) else ""
    return sihua_item(raw) if raw else None


def _build_bazi(bazi: Dict[str, Any]) -> Dict[str, Any]:
    if not bazi:
        return {}
    detail = _list(_seg(bazi.get("enhanced_analysis")).get("四柱详析"))
    nayin = _seg(bazi.get("nayin"))
    ten_gods = _seg(bazi.get("ten_gods"))
    pillar_keys = ["year", "month", "day", "hour"]
    label_cn = ["年柱", "月柱", "日柱", "时柱"]
    pillars = []
    for i, key in enumerate(pillar_keys):
        raw_pair = bazi.get(f"{key}_pillar", "")
        det = _seg(detail[i]) if i < len(detail) else {}
        hidden_gods = [
            {"stem": stem_item(_seg(hg).get("藏干")),
             "god": tengod_item(_seg(hg).get("十神"))}
            for hg in _list(det.get("藏干十神"))
        ]
        pillars.append({
            "key": key,
            "label": PILLAR_LABEL_EN[label_cn[i]],
            "pair": pillar_pair(raw_pair),
            "stem": stem_item(raw_pair[0] if isinstance(raw_pair, str) and len(raw_pair) >= 1 else ""),
            "branch": branch_item(raw_pair[1] if isinstance(raw_pair, str) and len(raw_pair) >= 2 else ""),
            "nayin": nayin_text(det.get("纳音") or nayin.get(label_cn[i], "")),
            "hidden_stems": [stem_item(s) for s in _list(det.get("藏干"))],
            "hidden_gods": hidden_gods,
            "ten_god": tengod_item(ten_gods.get(f"{label_cn[i][0]}干", "")),
            "main_god": tengod_item(det.get("主星", "")),
            "growth_state": (_pair(GROWTH_STATE_EN[det["星运（十二长生）"]], det["星运（十二长生）"])
                             if det.get("星运（十二长生）") in GROWTH_STATE_EN else det.get("星运（十二长生）")),
            "void": VOID_EN.get(det.get("空亡", ""), det.get("空亡", "")),
        })
    elements_src = _seg(bazi.get("five_elements")) or _seg(bazi.get("five_elements_count"))
    dayun = _seg(bazi.get("dayun"))
    note_raw = dayun.get("note", "")
    return {
        "pillars": pillars,
        "day_master": stem_item(bazi.get("day_master", "")),
        "body_strength": STRENGTH_EN.get(bazi.get("body_strength", ""), bazi.get("body_strength", "")),
        "five_elements": [
            {"key": k, "text": (_pair(ELEMENT_EN[k], k) if k in ELEMENT_EN else k), "count": v}
            for k, v in elements_src.items()
        ],
        "ten_gods": [
            {"position": STEM_POSITION_EN.get(pos, pos), "god": tengod_item(god)}
            for pos, god in ten_gods.items()
        ],
        "spirits": [_named(SPIRIT_EN, s) for s in _list(bazi.get("spirits"))],
        "dayun": {
            "direction": DIRECTION_EN.get(dayun.get("direction", ""), dayun.get("direction", "")),
            "qiyun_age": dayun.get("qiyun_age"),
            "note": NOTE_EN.get(note_raw, "" if note_raw in _PLACEHOLDERS else note_raw),
        },
        "lunar_date": None if bazi.get("lunar_date") in _PLACEHOLDERS else bazi.get("lunar_date"),
    }


def _build_ziwei(ziwei: Dict[str, Any]) -> Dict[str, Any]:
    if not ziwei:
        return {}
    basic = _seg(ziwei.get("basic_info"))
    chart = _seg(ziwei.get("chart"))
    palaces_raw = _seg(chart.get("palaces"))
    palaces = []
    for name, pal in palaces_raw.items():
        pal = _seg(pal)
        palaces.append({
            "name": palace_item(name),
            "index": pal.get("index"),
            "is_body_palace": bool(pal.get("is_body_palace")),
            "stem": stem_item(pal.get("heavenly_stem", "")),
            "branch": branch_item(pal.get("earthly_branch", "")),
            "major_stars": [
                {"name": star_item(_seg(s).get("name", "")),
                 "brightness": _brightness_text(_seg(s).get("brightness", "")),
                 "mutagen": _mutagen_item(_seg(s).get("mutagen", ""))}
                for s in _list(pal.get("major_stars"))
            ],
            "minor_stars": [star_item(s) for s in _list(pal.get("minor_stars"))],
            "adjective_stars": [star_item(s) for s in _list(pal.get("adjective_stars"))],
        })
    four_trans = _seg(ziwei.get("year_four_trans"))
    bfuncs = _seg(ziwei.get("B_functions"))
    cfuncs = _seg(ziwei.get("C_functions"))
    flow_year = {}
    for k, v in bfuncs.items():
        if k.startswith("flow_year") and isinstance(v, dict):
            flow_year = {
                "palace": palace_item(v.get("palace", "")),
                "branch": branch_item(v.get("earthly_branch", "")),
                "major_stars": [star_item(s) for s in _list(v.get("major_stars"))],
                "minor_stars": [star_item(s) for s in _list(v.get("minor_stars"))],
            }
    flow_trans = {}
    for k, v in bfuncs.items():
        if k.startswith("flow_trans") and isinstance(v, dict):
            flow_trans = [{"type": sihua_item(t), "star": star_item(s)} for t, s in v.items()]
    return {
        "basic": {
            "soul": star_item(basic.get("soul", "")),
            "body": star_item(basic.get("body", "")),
            "five_elements_class": five_elements_class_text(basic.get("five_elements_class", "")),
            "lunar_date": lunar_date_en(basic.get("lunar_date", "")),
            "chinese_date": " · ".join(
                pillar_pair(p) for p in str(basic.get("chinese_date", "")).split(" ") if p
            ),
        },
        "year_four_trans": [
            {"type": sihua_item(t), "star": star_item(s)} for t, s in four_trans.items()
        ],
        "star_positions": [
            {"star": star_item(star), "palace": palace_item(pal)}
            for star, pal in _seg(chart.get("star_positions")).items()
        ],
        "palaces": palaces,
        "flow": {
            "major_fortune_palace": palace_item(bfuncs.get("major_fortune_25", "")),
            "house_of_flow": palace_item(bfuncs.get("house_of_flow_2024", "")),
            "flow_year": flow_year,
            "flow_trans": flow_trans,
            "tri_house_life": [palace_item(p) for p in _list(cfuncs.get("tri_house_ming"))],
            "star_tri_house_example": [palace_item(p) for p in _list(cfuncs.get("star_tri_house_example"))],
            "star_position_example": palace_item(_seg(ziwei.get("A_functions")).get("star_position_example", "")),
        },
        "features": ZIWEI_FEATURES_EN,
    }


def build_display(data: Dict[str, Any]) -> Dict[str, Any]:
    """由 calculate 原始输出构建英文展示树。原始 data 不做任何修改。

    结构与 ResultsPage 的渲染一一对应；每个术语条目为 {text, key}，
    text 是英译展示串，key 是原始中文值（前端据此挂 glossary 词条）。
    吠陀盘的盘面值（行星/星座/宫位）后端原生即英文，无需映射，
    这里仅翻译其 enhanced_features 的开发说明串。
    """
    data = _seg(data)
    inp = _seg(data.get("input"))
    vedic = _seg(data.get("vedic"))
    display: Dict[str, Any] = {
        "gender": GENDER_EN.get(inp.get("gender_str", ""), inp.get("gender_str", "")),
        "bazi": _build_bazi(_seg(data.get("bazi"))),
        "ziwei": _build_ziwei(_seg(data.get("ziwei"))),
    }
    if vedic:
        display["vedic"] = {"note": VEDIC_NOTE_EN, "features": VEDIC_FEATURES_EN}
    return display

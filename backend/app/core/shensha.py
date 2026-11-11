# -*- coding: utf-8 -*-
"""
八字神煞检测（查表数据来自 ShousenZHANG/chinese-fortune 的 assets/shensha.json，
MIT 许可，表内附三命通会/渊海子平出处考据；检测逻辑与释义为 lifeinsight 自撰）。
起法口径：日干系查四柱地支；三合系以年支与日支双查；天德/月德查四柱天干；
红鸾/天喜/孤辰/寡宿以年支起。空亡按日柱所在旬计算。
"""
from typing import Any, Dict, List

TABLES = {'天乙贵人': {'甲': ['丑', '未'], '戊': ['丑', '未'], '庚': ['丑', '未'], '乙': ['子', '申'], '己': ['子', '申'], '丙': ['亥', '酉'], '丁': ['亥', '酉'], '壬': ['卯', '巳'], '癸': ['卯', '巳'], '辛': ['午', '寅']}, '文昌贵人': {'甲': '巳', '乙': '午', '丙': '申', '戊': '申', '丁': '酉', '己': '酉', '庚': '亥', '辛': '子', '壬': '寅', '癸': '卯'}, '太极贵人': {'甲': ['子', '午'], '乙': ['子', '午'], '丙': ['卯', '酉'], '丁': ['卯', '酉'], '戊': ['辰', '戌', '丑', '未'], '己': ['辰', '戌', '丑', '未'], '庚': ['寅', '亥'], '辛': ['寅', '亥'], '壬': ['巳', '申'], '癸': ['巳', '申']}, '福星贵人': {'甲': '寅', '乙': '丑', '丙': '子', '丁': '酉', '戊': '申', '己': '未', '庚': '午', '辛': '巳', '壬': '辰', '癸': '卯'}, '国印贵人': {'甲': '戌', '乙': '亥', '丙': '丑', '丁': '寅', '戊': '丑', '己': '寅', '庚': '辰', '辛': '巳', '壬': '未', '癸': '申'}, '学堂': {'甲': '亥', '乙': '午', '丙': '寅', '丁': '酉', '戊': '寅', '己': '酉', '庚': '巳', '辛': '子', '壬': '申', '癸': '卯'}, '词馆': {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳', '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}, '天德贵人': {'寅月': '丁', '卯月': '申', '辰月': '壬', '巳月': '辛', '午月': '亥', '未月': '甲', '申月': '癸', '酉月': '寅', '戌月': '丙', '亥月': '乙', '子月': '巳', '丑月': '庚'}, '月德贵人': {'寅午戌': '丙', '申子辰': '壬', '巳酉丑': '庚', '亥卯未': '甲'}, '天德合': {'寅月': '壬', '卯月': '巳', '辰月': '丁', '巳月': '丙', '午月': '寅', '未月': '己', '申月': '戊', '酉月': '亥', '戌月': '辛', '亥月': '庚', '子月': '申', '丑月': '乙'}, '月德合': {'寅午戌': '辛', '申子辰': '丁', '巳酉丑': '乙', '亥卯未': '己'}, '天厨贵人': {'甲': '巳', '乙': '午', '丙': '子', '丁': '巳', '戊': '午', '己': '申', '庚': '寅', '辛': '午', '壬': '酉', '癸': '亥'}, '红鸾': {'子': '卯', '丑': '寅', '寅': '丑', '卯': '子', '辰': '亥', '巳': '戌', '午': '酉', '未': '申', '申': '未', '酉': '午', '戌': '巳', '亥': '辰'}, '天喜': {'子': '酉', '丑': '申', '寅': '未', '卯': '午', '辰': '巳', '巳': '辰', '午': '卯', '未': '寅', '申': '丑', '酉': '子', '戌': '亥', '亥': '戌'}, '金舆': {'甲': '辰', '乙': '巳', '丙': '未', '丁': '申', '戊': '未', '己': '申', '庚': '戌', '辛': '亥', '壬': '丑', '癸': '寅'}, '羊刃': {'甲': '卯', '乙': '寅', '丙': '午', '丁': '巳', '戊': '午', '己': '巳', '庚': '酉', '辛': '申', '壬': '子', '癸': '亥'}, '飞刃': {'甲': '酉', '乙': '申', '丙': '子', '丁': '亥', '戊': '子', '己': '亥', '庚': '卯', '辛': '寅', '壬': '午', '癸': '巳'}, '劫煞': {'申子辰': '巳', '寅午戌': '亥', '巳酉丑': '寅', '亥卯未': '申'}, '灾煞': {'申子辰': '午', '寅午戌': '子', '巳酉丑': '卯', '亥卯未': '酉'}, '桃花咸池': {'申子辰': '酉', '寅午戌': '卯', '巳酉丑': '午', '亥卯未': '子'}, '红艳煞': {'甲': '午', '乙': '申', '丙': '寅', '丁': '未', '戊': '辰', '己': '辰', '庚': '戌', '辛': '酉', '壬': '子', '癸': '申'}, '孤辰': {'亥子丑': '寅', '寅卯辰': '巳', '巳午未': '申', '申酉戌': '亥'}, '寡宿': {'亥子丑': '戌', '寅卯辰': '丑', '巳午未': '辰', '申酉戌': '未'}, '驿马': {'申子辰': '寅', '寅午戌': '申', '巳酉丑': '亥', '亥卯未': '巳'}, '华盖': {'申子辰': '辰', '寅午戌': '戌', '巳酉丑': '丑', '亥卯未': '未'}, '将星': {'申子辰': '子', '寅午戌': '午', '巳酉丑': '酉', '亥卯未': '卯'}, '亡神': {'申子辰': '亥', '寅午戌': '巳', '巳酉丑': '申', '亥卯未': '寅'}, '大耗': {'子': '未', '丑': '申', '寅': '酉', '卯': '戌', '辰': '亥', '巳': '子', '午': '丑', '未': '寅', '申': '卯', '酉': '辰', '戌': '巳', '亥': '午'}, '小耗': {'子': '巳', '丑': '午', '寅': '未', '卯': '申', '辰': '酉', '巳': '戌', '午': '亥', '未': '子', '申': '丑', '酉': '寅', '戌': '卯', '亥': '辰'}}

KONG_WANG = [{'xun': '甲子旬', 'from': '甲子', 'to': '癸酉', 'kong': ['戌', '亥'], 'source_review': {'status': 'arithmetic_definition', 'basis': '十干配十二支，每旬未配的两支', 'historical_attribution': 'pending', 'facsimile_status': 'not_checked'}}, {'xun': '甲戌旬', 'from': '甲戌', 'to': '癸未', 'kong': ['申', '酉'], 'source_review': {'status': 'arithmetic_definition', 'basis': '十干配十二支，每旬未配的两支', 'historical_attribution': 'pending', 'facsimile_status': 'not_checked'}}, {'xun': '甲申旬', 'from': '甲申', 'to': '癸巳', 'kong': ['午', '未'], 'source_review': {'status': 'arithmetic_definition', 'basis': '十干配十二支，每旬未配的两支', 'historical_attribution': 'pending', 'facsimile_status': 'not_checked'}}, {'xun': '甲午旬', 'from': '甲午', 'to': '癸卯', 'kong': ['辰', '巳'], 'source_review': {'status': 'arithmetic_definition', 'basis': '十干配十二支，每旬未配的两支', 'historical_attribution': 'pending', 'facsimile_status': 'not_checked'}}, {'xun': '甲辰旬', 'from': '甲辰', 'to': '癸丑', 'kong': ['寅', '卯'], 'source_review': {'status': 'arithmetic_definition', 'basis': '十干配十二支，每旬未配的两支', 'historical_attribution': 'pending', 'facsimile_status': 'not_checked'}}, {'xun': '甲寅旬', 'from': '甲寅', 'to': '癸亥', 'kong': ['子', '丑'], 'source_review': {'status': 'arithmetic_definition', 'basis': '十干配十二支，每旬未配的两支', 'historical_attribution': 'pending', 'facsimile_status': 'not_checked'}}]

_DAY_STEM_SHA = ["天乙贵人", "文昌贵人", "太极贵人", "福星贵人", "国印贵人", "学堂",
                 "词馆", "天厨贵人", "金舆", "羊刃", "飞刃", "红艳煞"]
_SANHE_SHA = ["劫煞", "灾煞", "桃花咸池", "驿马", "华盖", "将星", "亡神"]
_SANHUI_SHA = ["孤辰", "寡宿"]
_YEAR_BRANCH_SHA = ["红鸾", "天喜"]
_MONTH_STEM_SHA = ["天德贵人", "月德贵人", "天德合", "月德合"]
_SANHE_GROUPS = ["申子辰", "寅午戌", "巳酉丑", "亥卯未"]
_SANHUI_GROUPS = ["亥子丑", "寅卯辰", "巳午未", "申酉戌"]
_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"

GLOSS = {
    "天乙贵人": "天乙贵人主逢凶化吉：关键时刻易得有力之人相助",
    "文昌贵人": "文昌贵人主学业文才：利考试、写作与证书",
    "太极贵人": "太极贵人主悟性与玄学缘：对命理、哲学类学问易上手",
    "福星贵人": "福星贵人主衣食福气：一生少有断炊之忧",
    "国印贵人": "国印贵人主权柄与信用：宜体制、公职与掌印之务",
    "学堂": "学堂主向学与功名：学习吸收能力强",
    "词馆": "词馆主文辞表达：写作、策划、表达型工作有天赋加成",
    "天厨贵人": "天厨贵人主食禄：衣食丰足，亦利餐饮美食方向",
    "金舆": "金舆主富贵与享受：生活品质要求高，也易得之",
    "天德贵人": "天德贵人主逢凶化吉、心地仁厚：灾厄易解",
    "月德贵人": "月德贵人主平顺得助：一生近贵、少大风浪",
    "天德合": "天德合主暗中之助：化险多在不经意间",
    "月德合": "月德合主阴德庇佑：顺境不显、逆境有靠",
    "红鸾": "红鸾主婚喜人缘：感情机会与喜庆之事多",
    "天喜": "天喜主喜事临门：婚恋、添丁、晋升类喜事易近",
    "羊刃": "羊刃主刚烈与魄力：决断力强，但冲动与外伤风险也要管",
    "飞刃": "飞刃主突发与锋芒：行事宜留余地，防意外磕碰",
    "红艳煞": "红艳煞主魅力与情缘：异性缘旺，感情选择也多",
    "桃花咸池": "桃花主人缘与魅力：社交场合易得关注",
    "驿马": "驿马主走动变迁：异地、出行、变动中得机会",
    "华盖": "华盖主才艺与孤高：利钻研、艺术与玄学",
    "将星": "将星主领导力：适合带团队、担责",
    "劫煞": "劫煞主竞争损耗：合作与投资需防被人截胡",
    "灾煞": "灾煞主突发波折：重大事项宜留备选方案",
    "亡神": "亡神主心思深沉：利谋略但易多虑",
    "孤辰": "孤辰主独立与晚婚倾向：亲缘节奏慢热，重自我空间",
    "寡宿": "寡宿主独处与专注：利钻研，感情上慢热被动",
    "空亡": "空亡主先空后实：落空亡的宫位事项宜务实、忌画饼",
    "魁罡": "魁罡日主刚毅果断：魄力过人，宜管好锋芒与脾气",
    "三奇贵人": "三奇贵人主聪明奇才：思路非常规，易在专门领域出头",
}


def _group_of(branch: str, groups: List[str]) -> str:
    for g in groups:
        if branch in g:
            return g
    return ""


def detect_shensha(bazi: Dict[str, Any]) -> List[str]:
    """输入 bazi 载荷（四柱/日主），输出命中的神煞名列表（去重、吉神在前）。"""
    pillars = {}
    for key in ("year_pillar", "month_pillar", "day_pillar", "hour_pillar"):
        v = str(bazi.get(key, "") or "")
        if len(v) >= 2:
            pillars[key] = v
    if "day_pillar" not in pillars:
        return []
    day_master = str(bazi.get("day_master", "") or pillars["day_pillar"][0])
    stems = [p[0] for p in pillars.values()]
    branches = [p[1] for p in pillars.values()]
    year_branch = pillars.get("year_pillar", "  ")[1]
    day_branch = pillars["day_pillar"][1]
    month_branch = pillars.get("month_pillar", "  ")[1]
    hits: List[str] = []

    def hit(name: str):
        if name not in hits:
            hits.append(name)

    # 日干系：目标地支见于四柱
    for name in _DAY_STEM_SHA:
        targets = TABLES.get(name, {}).get(day_master)
        if targets and any(b in targets for b in branches):
            hit(name)
    # 三合系：以年支、日支所在三合组查，被查支见于四柱
    for name in _SANHE_SHA:
        table = TABLES.get(name, {})
        for base in (year_branch, day_branch):
            target = table.get(_group_of(base, _SANHE_GROUPS))
            if target and target in branches:
                hit(name)
                break
    # 三会系（孤辰寡宿）：以年支三会组查
    for name in _SANHUI_SHA:
        target = TABLES.get(name, {}).get(_group_of(year_branch, _SANHUI_GROUPS))
        if target and target in branches:
            hit(name)
    # 年支系（红鸾天喜）
    for name in _YEAR_BRANCH_SHA:
        target = TABLES.get(name, {}).get(year_branch)
        if target and target in branches:
            hit(name)
    # 月系（天德等）：目标天干见于四柱
    month_key = month_branch + "月"
    for name in _MONTH_STEM_SHA:
        table = TABLES.get(name, {})
        target = table.get(month_key) or table.get(_group_of(month_branch, _SANHE_GROUPS))
        if target and target in stems:
            hit(name)
    # 魁罡：日柱特定干支
    if pillars["day_pillar"] in ("庚辰", "庚戌", "壬辰", "戊戌"):
        hit("魁罡")
    # 三奇贵人：年月日三干成组
    trio = set(stems[:3])
    if any(set(t) <= trio for t in ("甲戊庚", "乙丙丁", "壬癸辛")):
        hit("三奇贵人")
    # 空亡：日柱旬空之支见于四柱
    try:
        gz_index = [i for i in range(60)
                    if _GAN[i % 10] == pillars["day_pillar"][0] and _ZHI[i % 12] == day_branch][0]
        xun_start = gz_index - (gz_index % 10)
        xun_name = _GAN[xun_start % 10] + _ZHI[xun_start % 12] + "旬"
        for kw in KONG_WANG:
            if kw.get("xun") == xun_name and any(b in kw.get("kong", []) for b in branches):
                hit("空亡")
                break
    except Exception:
        pass
    return hits

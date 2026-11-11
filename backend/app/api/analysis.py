from .prompt_admin import PROMPTS_DIR
from fastapi import APIRouter, Depends, HTTPException
from core.ratelimit import rate_limit
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import json
import os

# 如果有OpenAI API key，取消注释以下行
# import openai
# from openai import OpenAI

router = APIRouter()

class AnalysisRequest(BaseModel):
    chart_data: Dict[str, Any] = Field(..., description="三盘数据")
    analysis_type: str = Field(..., description="分析类型：personality, career, relationship, health, comprehensive")
    custom_question: Optional[str] = Field("", description="自定义问题")

class MindMapRequest(BaseModel):
    chart_data: Dict[str, Any] = Field(..., description="三盘数据")
    focus_area: Optional[str] = Field("comprehensive", description="关注领域")

@router.post("/chatgpt", dependencies=[Depends(rate_limit("chatgpt", 5, 60))])
async def analyze_with_chatgpt(request: AnalysisRequest):
    """
    使用ChatGPT分析命盘数据
    
    注意：需要设置环境变量 OPENAI_API_KEY
    """
    try:
        # 检查是否配置了API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                "success": False,
                "message": "未配置OpenAI API Key，请在环境变量中设置 OPENAI_API_KEY",
                "data": {
                    "analysis": "ChatGPT分析功能暂不可用，请配置API Key后使用。",
                    "suggestions": [
                        "在系统环境变量中设置 OPENAI_API_KEY",
                        "重启后端服务",
                        "或使用本地分析功能"
                    ]
                }
            }
        
        # TODO: 实现ChatGPT分析逻辑
        # client = OpenAI(api_key=api_key)
        
        # 构建分析提示
        analysis_prompt = _build_analysis_prompt(request.chart_data, request.analysis_type, request.custom_question)
        
        # 模拟分析结果（实际应该调用OpenAI API）
        mock_analysis = _generate_mock_analysis(request.analysis_type, request.chart_data)
        
        return {
            "success": True,
            "data": {
                "analysis": mock_analysis,
                "analysis_type": request.analysis_type,
                "timestamp": "2024-01-01T00:00:00Z",
                "source": "ChatGPT (模拟)"
            },
            "message": "分析完成（当前为模拟数据）"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"分析失败: {str(e)}"
        )

@router.post("/mindmap")
async def generate_mindmap(request: MindMapRequest):
    """
    生成命理分析思维导图数据（Mermaid格式）
    """
    try:
        # 提取关键信息
        chart_summary = _extract_chart_summary(request.chart_data)
        
        # 生成Mermaid思维导图
        mindmap_data = _generate_mermaid_mindmap(chart_summary, request.focus_area)
        
        return {
            "success": True,
            "data": {
                "mindmap": mindmap_data,
                "format": "mermaid",
                "focus_area": request.focus_area,
                "summary": chart_summary
            },
            "message": "思维导图生成成功"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"思维导图生成失败: {str(e)}"
        )

@router.post("/local-analysis")
async def local_analysis(request: AnalysisRequest):
    """
    本地规则分析（不依赖外部API）
    """
    valid_types = {"personality", "career", "wealth", "relationship", "health", "comprehensive"}
    if request.analysis_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Unsupported analysis type: {request.analysis_type}. Options: {sorted(valid_types)}")
    try:
        analysis_result = _perform_local_analysis(request.chart_data, request.analysis_type)

        return {
            "success": True,
            "data": analysis_result,
            "message": "Quick reading complete"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Local analysis failed: {str(e)}"
        )

def _build_analysis_prompt(chart_data: Dict[str, Any], analysis_type: str, custom_question: str = "") -> str:
    """构建分析提示。正式模板存放在仓库外私有目录（PROMPTS_DIR/free_analysis.json），不随公开仓库分发；缺失时用中性简版。"""
    bazi_json = json.dumps(chart_data.get('bazi', {}), ensure_ascii=False, indent=2)
    ziwei_json = json.dumps(chart_data.get('ziwei', {}), ensure_ascii=False, indent=2)
    vedic_json = json.dumps(chart_data.get('vedic', {}), ensure_ascii=False, indent=2)
    tpl = None
    try:
        tpl_file = PROMPTS_DIR / "free_analysis.json"
        if tpl_file.exists():
            tpl = json.loads(tpl_file.read_text(encoding='utf-8'))
    except Exception:
        tpl = None
    if tpl:
        base_prompt = (tpl["base"]
                       .replace("{analysis_type}", analysis_type)
                       .replace("{bazi_json}", bazi_json)
                       .replace("{ziwei_json}", ziwei_json)
                       .replace("{vedic_json}", vedic_json))
    else:
        base_prompt = f"请基于以下命盘数据进行{analysis_type}分析：\n\n八字信息：{bazi_json}\n\n紫微斗数：{ziwei_json}\n\n印度星盘：{vedic_json}"
        tpl = None
    if custom_question:
        base_prompt += f"\n\n特别关注：{custom_question}"
    if tpl:
        focus = tpl.get("focus", {}).get(analysis_type)
        if focus:
            base_prompt += f"\n\n{focus}"
    return base_prompt

def _generate_mock_analysis(analysis_type: str, chart_data: Dict[str, Any]) -> str:
    """生成模拟分析结果"""
    
    # 提取基本信息
    bazi_info = chart_data.get('bazi', {})
    ziwei_info = chart_data.get('ziwei', {})
    
    mock_templates = {
        "personality": f"""
        性格分析报告：
        
        根据您的八字和紫微斗数分析，您具有以下性格特点：
        
        1. 核心性格：
           - 八字显示您日主较强，具有独立自主的性格
           - 紫微斗数显示您的命宫主星组合体现出领导能力
        
        2. 天赋特质：
           - 思维敏捷，善于分析问题
           - 具有艺术天赋和审美能力
           - 人际交往能力较强
        
        3. 注意事项：
           - 有时过于追求完美
           - 需要注意情绪管理
           - 建议培养耐心和包容心
        """,
        
        "career": f"""
        事业发展分析：
        
        基于您的命盘特征，事业方面建议如下：
        
        1. 适合行业：
           - 金融、投资、管理类
           - 教育、咨询、策划类
           - 创意、设计、媒体类
        
        2. 发展时机：
           - 青年期（25-35岁）为事业发展黄金期
           - 中年期需要注意转型升级
        
        3. 成功要素：
           - 发挥沟通协调能力
           - 注重团队合作
           - 持续学习提升
        """,
        
        "comprehensive": f"""
        综合命理分析报告：
        
        1. 性格特征：独立自主，思维敏捷，具有领导潜质
        
        2. 事业发展：适合管理、金融、教育等行业，青年期为发展黄金期
        
        3. 感情婚姻：重视精神交流，理想化倾向，需要理解包容的伴侣
        
        4. 健康状况：总体良好，需注意心血管和消化系统保养
        
        5. 财运分析：理财能力较强，投资需谨慎，稳健为主
        
        6. 人际关系：社交能力强，贵人运不错，需要真诚待人
        """
    }
    
    return mock_templates.get(analysis_type, mock_templates["comprehensive"])

def _extract_chart_summary(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """提取命盘关键信息摘要"""
    
    summary = {
        "bazi_summary": {},
        "ziwei_summary": {},
        "vedic_summary": {}
    }
    
    # 提取八字摘要（字段与 /api/charts/calculate 的实际返回对齐；
    # 旧代码读的是中文键（四柱/日主…），真实返回是英文键，导致摘要恒为空）
    if not isinstance(chart_data, dict):
        chart_data = {}
    bazi = chart_data.get('bazi', {})
    if not isinstance(bazi, dict):
        bazi = {}
    if bazi:
        pillars = " ".join(x for x in [
            bazi.get('year_pillar', ''), bazi.get('month_pillar', ''),
            bazi.get('day_pillar', ''), bazi.get('hour_pillar', '')] if x)
        summary["bazi_summary"] = {
            "four_pillars": pillars,
            "day_master": bazi.get('day_master', ''),
            "strength": bazi.get('body_strength', ''),
            "five_elements": bazi.get('five_elements_count', {})
        }

    # 提取紫微摘要
    ziwei = chart_data.get('ziwei', {})
    if not isinstance(ziwei, dict):
        ziwei = {}
    if ziwei:
        star_positions = (ziwei.get('chart') or {}).get('star_positions', {})
        life_stars = [star for star, palace in star_positions.items() if palace == '命宫']
        basic = ziwei.get('basic_info', {})
        summary["ziwei_summary"] = {
            "life_palace": "、".join(life_stars),
            "body_palace": basic.get('body', ''),
            "major_stars": star_positions,
            "destiny_class": basic.get('five_elements_class', '')
        }

    # 提取印度星盘摘要
    vedic = chart_data.get('vedic', {})
    if not isinstance(vedic, dict):
        vedic = {}
    if vedic:
        planets = vedic.get('planets', {})
        summary["vedic_summary"] = {
            "ascendant": (vedic.get('ascendant') or {}).get('sign', ''),
            "sun_sign": (planets.get('Sun') or {}).get('sign', ''),
            "moon_sign": (planets.get('Moon') or {}).get('sign', ''),
            "planetary_positions": planets
        }

    return summary

def _generate_mermaid_mindmap(chart_summary: Dict[str, Any], focus_area: str) -> str:
    """生成Mermaid思维导图"""
    
    mindmap = """mindmap
  root((命理分析))
    八字系统
      四柱信息
        年柱
        月柱
        日柱
        时柱
      五行分析
        五行分布
        强弱分析
        用神忌神
    紫微斗数
      十二宫
        命宫
        财帛宫
        官禄宫
        田宅宫
      主星分布
        紫微星
        天机星
        太阳星
      四化飞星
        化禄
        化权
        化科
        化忌
    印度星盘
      十二星座
        白羊座
        金牛座
        双子座
        巨蟹座
      行星位置
        太阳
        月亮
        水星
        金星
      宫位分析
        第一宫
        第二宫
        第七宫
        第十宫
    综合分析
      性格特征
        优点
        缺点
        潜能
      事业发展
        适合行业
        发展时机
        注意事项
      感情婚姻
        感情观
        婚姻运
        桃花运
      健康状况
        体质特点
        易患疾病
        养生建议"""
    
    return mindmap

# ---------- 本地规则分析（无 Key 时的规则引擎，全部结论由盘面数据推导） ----------
# en-tree（英文站）：输出文案全量英化。查表逻辑与输入键一律不动（引擎输入
# 是中文盘面值，键保持中文）；只改输出字符串与含义表的值。展示名与
# i18n/chart_terms.py 的 display 树及 frontend glossary.js 标题对齐。

try:
    from ..i18n.chart_terms import (ELEMENT_EN as _CT_ELEMENT_EN, TEN_GOD_EN as _CT_TEN_GOD_EN,
                                    STAR_EN as _CT_STAR_EN, ADJECTIVE_STAR_EN as _CT_ADJ_STAR_EN,
                                    PALACE_EN as _CT_PALACE_EN, SIHUA_EN as _CT_SIHUA_EN,
                                    BRIGHTNESS_EN as _CT_BRIGHTNESS_EN, STEM_PINYIN as _CT_STEM_PINYIN,
                                    BRANCH_PINYIN as _CT_BRANCH_PINYIN,
                                    STEM_POSITION_EN as _CT_STEM_POSITION_EN, pillar_pair as _ct_pillar_pair)
except ImportError:
    try:
        from app.i18n.chart_terms import (ELEMENT_EN as _CT_ELEMENT_EN, TEN_GOD_EN as _CT_TEN_GOD_EN,
                                          STAR_EN as _CT_STAR_EN, ADJECTIVE_STAR_EN as _CT_ADJ_STAR_EN,
                                          PALACE_EN as _CT_PALACE_EN, SIHUA_EN as _CT_SIHUA_EN,
                                          BRIGHTNESS_EN as _CT_BRIGHTNESS_EN, STEM_PINYIN as _CT_STEM_PINYIN,
                                          BRANCH_PINYIN as _CT_BRANCH_PINYIN,
                                          STEM_POSITION_EN as _CT_STEM_POSITION_EN, pillar_pair as _ct_pillar_pair)
    except ImportError:
        from i18n.chart_terms import (ELEMENT_EN as _CT_ELEMENT_EN, TEN_GOD_EN as _CT_TEN_GOD_EN,
                                      STAR_EN as _CT_STAR_EN, ADJECTIVE_STAR_EN as _CT_ADJ_STAR_EN,
                                      PALACE_EN as _CT_PALACE_EN, SIHUA_EN as _CT_SIHUA_EN,
                                      BRIGHTNESS_EN as _CT_BRIGHTNESS_EN, STEM_PINYIN as _CT_STEM_PINYIN,
                                      BRANCH_PINYIN as _CT_BRANCH_PINYIN,
                                      STEM_POSITION_EN as _CT_STEM_POSITION_EN, pillar_pair as _ct_pillar_pair)

# 星曜英文别号（与 glossary.js 的 star 标题一致）；键为中文星名（查表键不动）
_STAR_EPITHET = {
    "紫微": "the Emperor Star", "天机": "the Strategist", "太阳": "the Sun Star",
    "武曲": "the Money-and-Action Star", "天同": "the Contentment Star", "廉贞": "the Intense Star",
    "天府": "the Treasury Star", "太阴": "the Moon Star", "贪狼": "the Desire Star",
    "巨门": "the Voice Star", "天相": "the Chancellor Star", "天梁": "the Shelter Star",
    "七杀": "the General Star", "破军": "the Change Star",
    "文昌": "the Scholar Star", "文曲": "the Artist Star", "左辅": "the Helper Star",
    "右弼": "the Support Star", "天魁": "the Patron Star", "天钺": "the Lucky Break Star",
    "禄存": "the Savings Star", "天马": "the Travel Star", "火星": "the Spark Star",
    "铃星": "the Smolder Star", "擎羊": "the Blade Star", "陀罗": "the Grind Star",
    "地空": "the Daydream Star", "地劫": "the Sudden-Change Star",
}


def _star_disp(name: str) -> str:
    """星名完整展示：'Zi Wei (紫微) · the Emperor Star'（与 glossary 标题一致）。"""
    en = _CT_STAR_EN.get(name) or _CT_ADJ_STAR_EN.get(name)
    if not en:
        return name
    ep = _STAR_EPITHET.get(name)
    return f"{en} ({name}) · {ep}" if ep else f"{en} ({name})"


def _star_short(name: str) -> str:
    """星名简短展示：'Zi Wei (紫微)'。"""
    en = _CT_STAR_EN.get(name) or _CT_ADJ_STAR_EN.get(name)
    return f"{en} ({name})" if en else name


def _palace_disp(name: str) -> str:
    """宫位展示：'Life Palace (命宫)' / 'Wealth Palace (财帛宫)'。"""
    en = _CT_PALACE_EN.get(name)
    if not en:
        return name
    glyph = name if name.endswith("宫") else name + "宫"
    return f"{en} ({glyph})"


def _el_disp(el: str) -> str:
    """五行展示：'Wood (木)'。"""
    en = _CT_ELEMENT_EN.get(el)
    return f"{en} ({el})" if en else el


def _god_disp(god: str) -> str:
    """十神展示：'Windfall Wealth (偏财)'（与 glossary 的 tengod 标题一致）。"""
    en = _CT_TEN_GOD_EN.get(god)
    return f"{en} ({god})" if en else god


# 宫位的生活领域说法（行文引用宫位时优先用领域说法，其次才用宫名）
_PALACE_AREA = {
    "命宫": "the self area", "兄弟": "the siblings-and-peers area", "夫妻": "the love-and-marriage area",
    "子女": "the children-and-creativity area", "财帛": "the money area", "疾厄": "the health area",
    "迁移": "the away-from-home area", "交友": "the friends-and-network area",
    "仆役": "the friends-and-network area", "官禄": "the career area",
    "田宅": "the home-and-property area", "福德": "the inner-life area",
    "父母": "the parents-and-elders area",
}

_GAN_ELEMENT = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
                "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
_ELEMENT_TRAIT = {
    "木": "kind and upright, focused on growth and long-term plans",
    "火": "warm and expressive, fast to act, cares about being seen and doing things properly",
    "土": "steady and practical, values trust and slow accumulation",
    "金": "decisive and principled, strong follow-through, clear boundaries",
    "水": "quick and adaptable, values information and flow",
}
_ELEMENT_ORGAN = {"木": "the liver, gallbladder and tendons", "火": "the heart, circulation and your sleep rhythm",
                  "土": "the stomach, spleen and digestion",
                  "金": "the lungs, airways and skin", "水": "the kidneys, urinary system and hormone balance"}
_ELEMENT_THEME = {"木": "growth and planning", "火": "visibility and pace", "土": "stability and accumulation",
                  "金": "rules and execution", "水": "information and movement"}
_STAR_TRAIT = {
    "紫微": "strong self-respect and a drive to be in charge", "天机": "a fast, planning mind that can overthink",
    "太阳": "loves the spotlight, generous, cares about reputation",
    "武曲": "practical and decisive, with a strong money sense", "天同": "gentle and easygoing, values comfort and good feelings",
    "廉贞": "a vivid personality — competitive, and deep in love",
    "天府": "steady and conservative, good at storing up resources", "太阴": "delicate and sensitive, with strong taste and intuition",
    "贪狼": "strong appetites, many talents, a wide social circle",
    "巨门": "sharp with words and analysis, but can be suspicious", "天相": "the steady supporter type — values promises and image",
    "天梁": "an elder's air — likes to look after people, strong on principles",
    "七杀": "bold and fast-moving, loves a challenge, dislikes being controlled", "破军": "tears down the old to build the new — big swings, strong at starting things",
    "左辅": "draws support — helpful people show up", "右弼": "draws support — helpful people show up",
    "文昌": "strong at writing and exams, a clear and orderly mind",
    "文曲": "eloquent and artistically talented", "天魁": "patrons and elders lend a hand",
    "天钺": "timely help and lucky breaks",
    "禄存": "carries its own steady income and earns steadily", "天马": "always on the move — chances come through motion",
    "擎羊": "strong drive, but can act on impulse", "陀罗": "drags and entangles — things tend to repeat and stall",
    "火星": "impatient, with explosive bursts of energy",
    "铃星": "a slow-burning inner fire — can bottle things up", "地空": "unconventional ideas, dislikes playing by the book",
    "地劫": "cares a lot about gains and losses — money can leak",
}
# 十二宫领域（四化落宫与宫位解读用）
_PALACE_DOMAIN = {
    "命宫": "you yourself and the main tone of your life", "兄弟": "siblings and peers or partners on your level",
    "夫妻": "love and marriage", "子女": "children and creative work",
    "财帛": "money and how you earn it", "疾厄": "health and your body's weak spots",
    "迁移": "life away from home and your public image", "交友": "friends and your network",
    "仆役": "friends and your network",
    "官禄": "career and social standing", "田宅": "home and property",
    "福德": "your inner world, rest and enjoyment", "父母": "parents and your bond with elders",
}
# 四化释义（生年四化落宫的读法）
_TRANS_MEANING = {
    "禄": "Lu is about ease and gain: this area tends to give, and you are happy to invest in it — one of life's sweet spots",
    "权": "Quan is about control and drive: this is the area where you most want the final say, and where your force lands",
    "科": "Ke is about reputation and helpful people: this area easily wins praise and support — good ground for building a name",
    "忌": "Ji is about attachment and homework: this is the area you cannot let go of and get stuck in most easily — a lesson to work on, not a disaster",
}
# 吠陀：星座基调 / 行星领域 / 宫位领域 / 星座主星
_SIGN_TRAIT_V = {
    "Aries": "direct, action-first — does first, thinks later", "Taurus": "practical, builds up steadily, enjoys the senses",
    "Gemini": "curious, a good talker, with wide interests", "Cancer": "values feelings and safety, protective of home",
    "Leo": "wants a stage and recognition, with strong pride", "Virgo": "detail-minded, values order and looking after health",
    "Libra": "relationship- and balance-focused, with good taste", "Scorpio": "deep and intense, with strong control and insight",
    "Sagittarius": "loves freedom and far places, runs on belief", "Capricorn": "patient and goal-driven — a late bloomer who lasts",
    "Aquarius": "independent, idea-driven, values its circle", "Pisces": "highly empathetic, imaginative, with soft boundaries",
}
_PLANET_DOMAIN_V = {
    "Sun": "the Sun (self and ambition)", "Moon": "the Moon (feelings and inner life)", "Mercury": "Mercury (mind and communication)",
    "Venus": "Venus (love and taste)", "Mars": "Mars (drive and nerve)", "Jupiter": "Jupiter (learning and mentors)",
    "Saturn": "Saturn (pressure and staying power)",
}
_PLANET_EN = {"Sun": "the Sun", "Moon": "the Moon", "Mercury": "Mercury", "Venus": "Venus",
              "Mars": "Mars", "Jupiter": "Jupiter", "Saturn": "Saturn"}
_DASHA_DOMAIN = {**_PLANET_DOMAIN_V,
                 "Rahu": "Rahu (appetite and ambition)", "Ketu": "Ketu (letting go and insight)"}
_HOUSE_DOMAIN_V = {
    1: "self-image", 2: "building wealth", 3: "communication and siblings", 4: "home and roots",
    5: "talent, romance and children", 6: "daily work and health", 7: "marriage and partnership",
    8: "windfall money, crises and turning points", 9: "far places, beliefs and mentors",
    10: "career and standing", 11: "income and your circle", 12: "retreat, quiet losses and life overseas",
}
_SIGN_LORD_V = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
_DASHA_EN = {"Ketu": "Ketu", "Venus": "Venus", "Sun": "Sun", "Moon": "Moon", "Mars": "Mars",
             "Rahu": "Rahu", "Jupiter": "Jupiter", "Saturn": "Saturn", "Mercury": "Mercury"}
# 五行生克：我克者为财，被我生者为食伤，克我者为官杀，生我者为印
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


_STEMS = "甲乙丙丁戊己庚辛壬癸"
_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
_BRANCH_ELEMENT = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
                   "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}


def _gz_index(stem: str, branch: str) -> int:
    """干支在六十甲子中的序号（0-59）。"""
    for i in range(60):
        if _STEMS[i % 10] == stem and _BRANCHES[i % 12] == branch:
            return i
    return -1


def _dayun_sequence(month_pillar: str, direction: str, qiyun_age: int, count: int = 6) -> list:
    """由月柱推大运干支序列：顺行/逆行逐位进退，每步十年。返回 [(干支, 起岁, 止岁)]。"""
    if not month_pillar or len(month_pillar) < 2 or direction not in ("顺", "逆"):
        return []
    idx = _gz_index(month_pillar[0], month_pillar[1])
    if idx < 0:
        return []
    step = 1 if direction == "顺" else -1
    out = []
    for k in range(1, count + 1):
        i = (idx + step * k) % 60
        start = qiyun_age + (k - 1) * 10
        out.append((f"{_STEMS[i % 10]}{_BRANCHES[i % 12]}", start, start + 9))
    return out


# 吠陀：行星旺/庙/陷（旺宫与入庙宫为传统定表）
_VEDIC_EXALT = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
                "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra"}
_VEDIC_OWN = {"Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
              "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
              "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"]}
_SIGNS_ORDER = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
                "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
# 27 星宿（Nakshatra）：名 + 宿主星（Vimshottari 大运由此宿主星起排）
_NAKSHATRAS = [
    ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"), ("Rohini", "Moon"),
    ("Mrigashira", "Mars"), ("Ardra", "Rahu"), ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"),
    ("Ashlesha", "Mercury"), ("Magha", "Ketu"), ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"), ("Vishakha", "Jupiter"),
    ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"), ("Mula", "Ketu"), ("Purva Ashadha", "Venus"),
    ("Uttara Ashadha", "Sun"), ("Shravana", "Moon"), ("Dhanishta", "Mars"), ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"), ("Revati", "Mercury"),
]
_DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
                "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
_DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]


def _vimshottari(moon_lon_abs: float, birth_year: int, birth_month: int, birth_day: int):
    """由月亮黄经推 Nakshatra 与当前 Vimshottari 大运（Mahadasha）。
    返回 (星宿名, 当前大运主星, 起始年, 结束年) 或 None。"""
    try:
        from datetime import date
        span = 360.0 / 27.0
        idx = int(moon_lon_abs // span) % 27
        nak_name, lord = _NAKSHATRAS[idx]
        frac = (moon_lon_abs - idx * span) / span
        birth = date(birth_year, birth_month, birth_day)
        elapsed = -(1.0 - frac) * _DASHA_YEARS[lord]  # 出生时第一大运的剩余从负偏移计
        periods = []
        pos = _DASHA_ORDER.index(lord)
        offset_years = (1.0 - frac) * _DASHA_YEARS[lord]
        # 第一段为出生时正在走的大运（只剩 offset_years）
        seq = [(lord, offset_years)]
        for k in range(1, 10):
            p = _DASHA_ORDER[(pos + k) % 9]
            seq.append((p, float(_DASHA_YEARS[p])))
        today = date.today()
        cursor = float(birth.year) + (birth.timetuple().tm_yday / 365.25)
        now_f = today.year + (today.timetuple().tm_yday / 365.25)
        for p, yrs in seq:
            if cursor + yrs > now_f:
                return nak_name, p, int(cursor), int(cursor + yrs)
            cursor += yrs
        return nak_name, seq[-1][0], int(cursor), int(cursor + seq[-1][1])
    except Exception:
        return None


def _palace_stars(star_positions: Dict[str, str], palace: str) -> list:
    return [s for s, p in (star_positions or {}).items() if p == palace]


def _perform_local_analysis(chart_data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
    """Execute the local rule analysis: every point is derived from the chart
    passed in; nothing is generic filler text.

    The data shape matches /api/charts/calculate (English keys in, Chinese
    chart values as lookup keys). When chart data is missing, the result says
    so plainly instead of inventing conclusions.
    """
    # 段必须是 dict：传字符串/列表等垃圾类型时降级为空，不许 500
    def _seg(v):
        return v if isinstance(v, dict) else {}
    chart_data = chart_data if isinstance(chart_data, dict) else {}
    bazi = _seg(chart_data.get("bazi"))
    ziwei = _seg(chart_data.get("ziwei"))
    vedic = _seg(chart_data.get("vedic"))
    gender = _seg(chart_data.get("input")).get("gender", 1)

    day_master = bazi.get("day_master", "")
    if not isinstance(day_master, str):
        day_master = ""
    dm_element = _GAN_ELEMENT.get(day_master, "")
    strength = bazi.get("body_strength", "")
    if not isinstance(strength, str):
        strength = ""
    elements = bazi.get("five_elements_count") or {}
    if not isinstance(elements, dict):
        elements = {}
    elements = {k: v for k, v in elements.items() if isinstance(v, (int, float))}
    ten_gods = bazi.get("ten_gods") or {}
    star_positions = (ziwei.get("chart") or {}).get("star_positions") or {}
    if not isinstance(star_positions, dict):
        star_positions = {}
    # Full star->palace map: star_positions holds only the 14 major stars, so a
    # birth-year transformation landing on a minor/adjective star (e.g. Wen Chang
    # carrying Ji, Wen Qu carrying Ke) could not be resolved to its palace and
    # fell back to "palace was not provided". Fill the gaps from the palaces
    # full star table (major + minor + adjective). setdefault keeps
    # star_positions authoritative for major stars, so major-star behaviour
    # is unchanged.
    all_star_positions = dict(star_positions)
    _palaces_all = (ziwei.get("chart") or {}).get("palaces") or {}
    if isinstance(_palaces_all, dict):
        for _pname, _pinfo in _palaces_all.items():
            if not isinstance(_pinfo, dict):
                continue
            for _skey in ("major_stars", "minor_stars", "adjective_stars"):
                for _st in _pinfo.get(_skey) or []:
                    _sname = _st.get("name") if isinstance(_st, dict) else _st
                    if isinstance(_sname, str) and _sname:
                        all_star_positions.setdefault(_sname, _pname)
    life_stars = _palace_stars(star_positions, "命宫")
    asc_sign = (vedic.get("ascendant") or {}).get("sign", "")
    # 紫微进阶数据：生年四化（星名）+ 命主/身主；四化落宫 = 该星所在宫位
    four_trans = ziwei.get("year_four_trans") or {}
    if not isinstance(four_trans, dict):
        four_trans = {}
    ziwei_basic = ziwei.get("basic_info") or {}
    soul_star = ziwei_basic.get("soul", "") if isinstance(ziwei_basic, dict) else ""
    body_star = ziwei_basic.get("body", "") if isinstance(ziwei_basic, dict) else ""

    def _trans_line(ttype: str) -> str:
        star = four_trans.get(ttype, "")
        if not star:
            return ""
        palace = all_star_positions.get(star, "")
        if not palace:
            return f"{_star_disp(star)} carries the {_CT_SIHUA_EN.get(ttype, ttype)} charge ({ttype}) — its palace was not provided"
        return (f"{_star_disp(star)} carries the {_CT_SIHUA_EN.get(ttype, ttype)} charge ({ttype}) "
                f"in the {_palace_disp(palace)} ({_PALACE_DOMAIN.get(palace, palace)}): {_TRANS_MEANING.get(ttype, '')}")

    def _trans_in_pairs(palace: str) -> list:
        """落在指定宫位的四化（返回 [(星名, 化)]，供逻辑判断用）"""
        out = []
        for t, star in four_trans.items():
            if star and all_star_positions.get(star) == palace:
                out.append((star, t))
        return out

    def _trans_in(palace: str) -> list:
        """落在指定宫位的四化（展示串，如 ['Tan Lang (贪狼) carrying Lu']）"""
        return [f"{_star_short(star)} carrying {_CT_SIHUA_EN.get(t, t)}" for star, t in _trans_in_pairs(palace)]

    # 八字进阶：神煞（引擎已算）、大运推排、喜用方向、当前年龄
    spirits = bazi.get("spirits") or []
    if not isinstance(spirits, list):
        spirits = []
    # 神煞全量检测（chinese-fortune 查表，MIT）与引擎自带结果合并去重
    try:
        from core.shensha import detect_shensha as _detect_shensha
        for _sp in _detect_shensha(bazi):
            if _sp not in spirits:
                spirits.append(_sp)
    except Exception:
        pass
    dayun_info = bazi.get("dayun") or {}
    month_pillar = bazi.get("month_pillar", "")
    birth_date_str = _seg(chart_data.get("input")).get("birth_date", "")
    age_now = None
    _birth_y = _birth_m = _birth_d = None
    try:
        from datetime import date as _date
        _bp = [int(x) for x in str(birth_date_str).split("-")]
        _birth_y, _birth_m, _birth_d = _bp[0], _bp[1], _bp[2]
        _today = _date.today()
        age_now = _today.year - _birth_y - ((_today.month, _today.day) < (_birth_m, _birth_d))
    except Exception:
        pass
    dayun_seq = []
    current_dayun = None
    if isinstance(dayun_info, dict) and month_pillar:
        dayun_seq = _dayun_sequence(month_pillar, str(dayun_info.get("direction", "")),
                                     int(dayun_info.get("qiyun_age", 0) or 0))
        if age_now is not None:
            for gz, a0, a1 in dayun_seq:
                if a0 <= age_now <= a1:
                    current_dayun = (gz, a0, a1)
    # 喜用方向（扶抑法简化）：身强喜克泄耗，身弱喜生扶
    xi_yong = ""
    if dm_element:
        gen_by = [k for k, v in _GENERATES.items() if v == dm_element]  # 生我者=印
        ctrl_by = [k for k, v in _CONTROLS.items() if v == dm_element]  # 克我者=官杀
        if strength == "强":
            xi_yong = (f"lean toward {_el_disp(_GENERATES.get(dm_element, ''))} (expressing yourself and letting talent out), "
                       f"{_el_disp(ctrl_by[0] if ctrl_by else '')} (structure, rules and discipline) and "
                       f"{_el_disp(_CONTROLS.get(dm_element, ''))} (money and resources)")
        elif strength == "弱":
            xi_yong = (f"lean toward {_el_disp(gen_by[0] if gen_by else '')} (support, learning and mentors) and "
                       f"{_el_disp(dm_element)} itself (peers, partners and doing it together)")
    # 神煞英文释义（键为中文神煞名，与 core.shensha 的检测输出对齐；不改 core 模块）
    _SPIRIT_GLOSS_EN = {
        "天乙贵人": "Tian Yi Gui Ren (天乙贵人): turns trouble aside — at the key moment, someone with real power tends to help",
        "文昌贵人": "Wen Chang Gui Ren (文昌贵人): study and writing luck — exams, writing and certificates go more smoothly",
        "太极贵人": "Tai Ji Gui Ren (太极贵人): a feel for the deeper patterns — philosophy and the unseen click for you quickly",
        "福星贵人": "Fu Xing Gui Ren (福星贵人): a basic floor of good fortune — you rarely have to worry about getting by",
        "国印贵人": "Guo Yin Gui Ren (国印贵人): authority and trust — institutions, official roles and carrying the seal suit you",
        "学堂": "Xue Tang (学堂): a learner's star — you absorb study and training fast",
        "词馆": "Ci Guan (词馆): a wordsmith's star — writing, planning and presenting get a talent bonus",
        "天厨贵人": "Tian Chu Gui Ren (天厨贵人): the star of good food and steady provision — and a plus for food-and-drink work",
        "金舆": "Jin Yu (金舆): comfort and quality — you hold a high bar for living standards, and tend to reach it",
        "天德贵人": "Tian De Gui Ren (天德贵人): a kind heart that turns trouble aside — hard knocks tend to soften",
        "月德贵人": "Yue De Gui Ren (月德贵人): a smoother road — helpful people stay near, big storms are rarer",
        "天德合": "Tian De He (天德合): quiet help — dangers tend to dissolve before you even notice them",
        "月德合": "Yue De He (月德合): protection earned in the background — invisible in good times, there in bad ones",
        "红鸾": "Hong Luan (红鸾): the wedding-and-romance star — love chances and happy occasions come more often",
        "天喜": "Tian Xi (天喜): happy news tends to find you — romance, children, promotions",
        "羊刃": "Yang Ren (羊刃): nerve and decisiveness — strong follow-through; keep an eye on impulse and bumps and scrapes",
        "飞刃": "Fei Ren (飞刃): sudden edges — leave yourself margin in fast-moving situations and watch for knocks",
        "红艳煞": "Hong Yan Sha (红艳煞): charisma and romantic pull — plenty of attention, and plenty of choices",
        "桃花咸池": "Tao Hua (桃花): charm and social magnetism — you get noticed in a crowd",
        "桃花": "Tao Hua (桃花): charm and social magnetism — you get noticed in a crowd",
        "驿马": "Yi Ma (驿马): the travel star — chances come through moving, trips and change",
        "华盖": "Hua Gai (华盖): talent with a solitary streak — deep study, art and the unseen suit you",
        "文昌": "Wen Chang (文昌): study and writing talent — exams, writing and certificates go more smoothly",
        "将星": "Jiang Xing (将星): a leader's star — built to lead a team and carry responsibility",
        "劫煞": "Jie Sha (劫煞): competitive losses — in partnerships and investments, guard against being cut out",
        "灾煞": "Zai Sha (灾煞): sudden wobbles — keep a backup plan for the big things",
        "亡神": "Wang Shen (亡神): a deep, strategising mind — good for planning, but watch the overthinking",
        "孤辰": "Gu Chen (孤辰): independence, and a slower warmth in close bonds — you need your own space",
        "寡宿": "Gua Su (寡宿): solitude and focus — good for deep work; slow to warm up in love",
        "空亡": "Kong Wang (空亡): emptiness first, substance later — in the areas it touches, stay practical and skip the pie in the sky",
        "魁罡": "Kui Gang (魁罡): a tough, decisive Day Master — real nerve; mind the sharp edge and the temper",
        "三奇贵人": "San Qi Gui Ren (三奇贵人): an unusual, quick mind — you stand out in specialised fields",
    }

    # 紫微深层：宫位全息表（排盘引擎已给宫干、身宫标记、星曜亮度与四化标记）
    palaces = (ziwei.get("chart") or {}).get("palaces") or {}
    if not isinstance(palaces, dict):
        palaces = {}
    body_palace_name = ""
    _idx2name = {}
    for _pn, _pi in palaces.items():
        if isinstance(_pi, dict):
            if _pi.get("is_body_palace"):
                body_palace_name = _pn
            if isinstance(_pi.get("index"), int):
                _idx2name[_pi["index"]] = _pn
    life_idx = None
    if isinstance(palaces.get("命宫"), dict):
        life_idx = palaces["命宫"].get("index")
    trine_palaces = []
    opp_palace = ""
    if isinstance(life_idx, int):
        trine_palaces = [_idx2name.get((life_idx + k) % 12, "") for k in (0, 4, 8)]
        opp_palace = _idx2name.get((life_idx + 6) % 12, "")

    def _major_stars_of(palace_name: str) -> list:
        pi = palaces.get(palace_name) or {}
        out = []
        if isinstance(pi, dict):
            for st in pi.get("major_stars") or []:
                if isinstance(st, dict) and st.get("name"):
                    out.append(st["name"])
        return out

    def _brightness_note(palace_name: str) -> str:
        pi = palaces.get(palace_name) or {}
        notes = []
        if isinstance(pi, dict):
            for st in pi.get("major_stars") or []:
                if isinstance(st, dict) and st.get("brightness") in ("庙", "旺", "陷"):
                    notes.append(f"{_star_short(st['name'])} at {_CT_BRIGHTNESS_EN.get(st['brightness'], st['brightness'])} brightness")
        return ", ".join(notes)

    # 十干四化表（中州派通行版；庚干科星诸家小异，此处取太阴）
    _STEM_TRANS = {
        "甲": {"禄": "廉贞", "权": "破军", "科": "武曲", "忌": "太阳"},
        "乙": {"禄": "天机", "权": "天梁", "科": "紫微", "忌": "太阴"},
        "丙": {"禄": "天同", "权": "天机", "科": "文昌", "忌": "廉贞"},
        "丁": {"禄": "太阴", "权": "天同", "科": "天机", "忌": "巨门"},
        "戊": {"禄": "贪狼", "权": "太阴", "科": "右弼", "忌": "天机"},
        "己": {"禄": "武曲", "权": "贪狼", "科": "天梁", "忌": "文曲"},
        "庚": {"禄": "太阳", "权": "武曲", "科": "太阴", "忌": "天同"},
        "辛": {"禄": "巨门", "权": "太阳", "科": "文曲", "忌": "文昌"},
        "壬": {"禄": "天梁", "权": "紫微", "科": "左辅", "忌": "武曲"},
        "癸": {"禄": "破军", "权": "巨门", "科": "太阴", "忌": "贪狼"},
    }

    def _fly_line(palace_name: str) -> str:
        """宫干飞化：该宫天干所化的禄/忌星飞入哪一宫（飞星派基本功）。"""
        pi = palaces.get(palace_name) or {}
        stem = pi.get("heavenly_stem", "") if isinstance(pi, dict) else ""
        trans = _STEM_TRANS.get(stem)
        if not trans:
            return ""
        parts = []
        for t in ("禄", "忌"):
            star = trans[t]
            dest = all_star_positions.get(star, "")
            if dest:
                parts.append(f"{_star_short(star)} carrying {_CT_SIHUA_EN.get(t, t)} flies into the {_palace_disp(dest)}")
        if not parts:
            return ""
        stem_disp = f"{_CT_STEM_PINYIN.get(stem, stem)} ({stem})" if stem else stem
        return (f"from the {_palace_disp(palace_name)} (stem {stem_disp}): " + "; ".join(parts)
                + " — where this palace opens, and where its homework sits, shows up in those areas")

    # 格局识别：移植 Renhuai123/ziwei-doushu patterns.ts 的严格判定
    # （MIT；四星全格与三星会分开，不再用自创的宽松阈值）
    # 英文站消费 *_en 平行字段（name_en/desc_en/breaking_en），缺失时回退中文字段
    try:
        from core.ziwei_patterns import detect as _zw_detect
        _raw_patterns = _zw_detect(palaces, (ziwei.get("year_four_trans") or {})) if palaces else []
    except Exception:
        _raw_patterns = []
    _lvl_rank = {"excellent": 0, "good": 1, "neutral": 2, "caution": 3}
    _raw_patterns = sorted(_raw_patterns, key=lambda p: _lvl_rank.get(p.get("level", ""), 4))
    patterns = []
    for _p in _raw_patterns:
        _desc = _p.get("desc_en") or _p.get("desc", "")
        if _p.get("breaking"):
            _br = _p.get("breaking_en") or _p.get("breaking")
            _desc += f" (Pattern note: {'; '.join(_br)})"
        patterns.append((_p.get("name_en") or _p.get("name", ""), _desc, _p.get("level", "")))

    # 吠陀进阶数据：行星 sign/house、按宫位聚合、月亮、上升主星落宫
    planets_v = vedic.get("planets") or {}
    if not isinstance(planets_v, dict):
        planets_v = {}
    houses_v: dict = {}
    for pname, pinfo in planets_v.items():
        if isinstance(pinfo, dict) and isinstance(pinfo.get("house"), int):
            houses_v.setdefault(pinfo["house"], []).append(pname)
    moon_info = planets_v.get("Moon") or {}
    moon_sign = moon_info.get("sign", "") if isinstance(moon_info, dict) else ""
    asc_lord = _SIGN_LORD_V.get(asc_sign, "")
    asc_lord_house = (planets_v.get(asc_lord) or {}).get("house") if asc_lord else None

    # 行星尊贵度（旺/庙/陷）与宫主飞入、Nakshatra 与当前大运
    # 条目为 (kind, text)：kind ∈ exalted/own/debilitated，供按类型筛选（原中文版按子串筛）
    dignity_lines = []
    for pname in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
        pinfo = planets_v.get(pname) or {}
        sign = pinfo.get("sign", "") if isinstance(pinfo, dict) else ""
        if not sign:
            continue
        if _VEDIC_EXALT.get(pname) == sign:
            dignity_lines.append(("exalted", f"{_PLANET_DOMAIN_V.get(pname, pname)} is exalted in {sign}: this side of you runs at its strongest — a real talent outlet"))
        elif sign in _VEDIC_OWN.get(pname, []):
            dignity_lines.append(("own", f"{_PLANET_DOMAIN_V.get(pname, pname)} is in its own sign {sign}: this side of you runs steadily, with solid footing"))
        elif _VEDIC_EXALT.get(pname) and _SIGNS_ORDER[(_SIGNS_ORDER.index(_VEDIC_EXALT[pname]) + 6) % 12] == sign:
            dignity_lines.append(("debilitated", f"{_PLANET_DOMAIN_V.get(pname, pname)} is debilitated in {sign}: this side of you starts out costlier to run and needs building up over time (a tendency, not a verdict)"))
    def _house_lord_line(house: int) -> str:
        if not asc_sign or asc_sign not in _SIGNS_ORDER:
            return ""
        sign = _SIGNS_ORDER[(_SIGNS_ORDER.index(asc_sign) + house - 1) % 12]
        lord = _SIGN_LORD_V.get(sign, "")
        lh = (planets_v.get(lord) or {}).get("house") if lord else None
        if not lord or not isinstance(lh, int):
            return ""
        if lh == house:
            return f"the lord of house {house} ({_HOUSE_DOMAIN_V.get(house, '')}) — {_PLANET_EN.get(lord, lord)} — sits in its own house: this area has firm roots and is mostly built by your own effort"
        return f"the lord of house {house} ({_HOUSE_DOMAIN_V.get(house, '')}) — {_PLANET_EN.get(lord, lord)} — has flown into house {lh} ({_HOUSE_DOMAIN_V.get(lh, '')}): {_HOUSE_DOMAIN_V.get(house, '')} and {_HOUSE_DOMAIN_V.get(lh, '')} are tied together in your life"
    dasha = None
    if isinstance(moon_info, dict) and moon_info.get("sign") in _SIGNS_ORDER and _birth_y:
        moon_abs = _SIGNS_ORDER.index(moon_info["sign"]) * 30 + float(moon_info.get("lon", 0) or 0)
        dasha = _vimshottari(moon_abs, _birth_y, _birth_m, _birth_d)

    def _house_line(house: int) -> str:
        ps = [p for p in houses_v.get(house, []) if p in _PLANET_DOMAIN_V]
        if not ps:
            return ""
        names = ", ".join(_PLANET_DOMAIN_V[p].split(" (")[0] for p in ps)
        return f"house {house} ({_HOUSE_DOMAIN_V.get(house, '')}) holds {names} — a lot of your story plays out in this area"

    dm_disp = ""
    if day_master:
        dm_disp = f"{_CT_STEM_PINYIN.get(day_master, day_master)} {_CT_ELEMENT_EN.get(dm_element, dm_element)} ({day_master})"
    strength_en = {"强": "strong", "弱": "weak"}.get(strength, "")

    basis = []
    if day_master:
        basis.append(f"Day Master {dm_disp} · {strength_en or 'strength not rated'}")
    if elements:
        basis.append("Elements: " + ", ".join(f"{_CT_ELEMENT_EN.get(k, k)} {v}" for k, v in elements.items()))
    if life_stars:
        basis.append("Life Palace stars: " + ", ".join(_star_short(s) for s in life_stars))
    if asc_sign:
        basis.append(f"Vedic rising sign: {asc_sign}")
    for _t in ("禄", "权", "科", "忌"):
        _st = four_trans.get(_t, "")
        if _st and all_star_positions.get(_st):
            basis.append(f"{_star_short(_st)} carrying {_CT_SIHUA_EN.get(_t, _t)} in the {_palace_disp(all_star_positions[_st])}")
    if moon_sign:
        basis.append(f"Moon in {moon_sign}")

    result = {
        "summary": "",
        "key_points": [],
        "suggestions": [],
        "confidence": "medium" if basis else "low",
        "basis": basis,
    }
    if not basis:
        result["summary"] = "Chart data is missing, so no rule-based reading can be made. Please complete a chart calculation first, then request the quick reading."
        return result

    strongest = max(elements, key=elements.get) if elements else ""
    weakest = min(elements, key=elements.get) if elements else ""
    god_names = list(ten_gods.values())
    star_line = ""
    if life_stars:
        traits = [_STAR_TRAIT[s] for s in life_stars if s in _STAR_TRAIT]
        if traits:
            star_line = f"Life Palace stars — {', '.join(_star_disp(s) for s in life_stars)}: {'; '.join(traits)}"

    if analysis_type == "personality":
        result["summary"] = (f"Your Day Master is {dm_disp} and it is {strength_en or 'not rated for strength'}: "
                             "the base color of your character comes from its element and from the major stars in your Life Palace.")
        result["key_points"] = [
            f"Day Master {dm_disp}: {_ELEMENT_TRAIT.get(dm_element, '')}",
            (f"Strength: {strength_en} — " + ("you have plenty of your own fuel and strong opinions; you tend to push forward on your own initiative" if strength == "强" else "your own fuel runs lower, so you do better riding a good environment and platform than carrying everything alone") if strength else "Day Master strength was not rated in this chart"),
            star_line or "Life Palace major-star data was not provided",
            f"Your strongest element is {_el_disp(strongest)} — that side of you shows the most; {_el_disp(weakest)} is the weakest, your relative blind side",
        ]
        result["suggestions"] = [
            f"When you lean on your {_el_disp(strongest)} strengths, watch for overdoing them; before a big decision, deliberately gather the {_el_disp(weakest)} side of the picture first",
            "Every point above names its basis (Day Master, Life Palace, elements) — keep what matches your real life and drop what does not",
        ]
    elif analysis_type == "career":
        month_god = ten_gods.get("月干", "")
        career_stars = _palace_stars(star_positions, "官禄")
        result["summary"] = (f"Career reads from the month pillar's ten god and the Career Palace: "
                             f"the month stem carries {_god_disp(month_god) if month_god else 'no data'}, "
                             f"and the Career Palace holds {', '.join(_star_short(s) for s in career_stars) or 'no data'}.")
        result["key_points"] = [
            f"Your month-stem ten god is {_god_disp(month_god)} — the main signal for the shape of your career from youth into midlife" if month_god else "Month-pillar ten-god data was not provided",
            ("The authority stars (官杀) are in your chart: you tend to do well inside systems with clear rules and a real promotion ladder" if any(g in god_names for g in ["正官", "七杀"]) else "The authority stars (官杀) do not stand out: you are more likely to build a career on professional skill or on running something of your own"),
            ("The expression stars (食伤) are in your chart: what you say, make and produce is your career capital" if any(g in god_names for g in ["食神", "伤官"]) else "The expression stars (食伤) do not stand out: your career capital leans more toward execution and pulling resources together"),
            (f"Your Career Palace holds {', '.join(_star_disp(s) for s in career_stars)}: " + "; ".join(_STAR_TRAIT[s] for s in career_stars if s in _STAR_TRAIT)) if career_stars else "Career Palace major-star data was not provided",
        ]
        result["suggestions"] = [
            f"For industries, start with fields that generate or match your {_el_disp(dm_element)} energy, and think twice before spending years in roles that fight your chart's costly directions head-on",
            "These are directional conclusions from chart rules — weigh them against your actual skills and the market in front of you",
        ]
    elif analysis_type == "wealth":
        wealth_element = _CONTROLS.get(dm_element, "")
        has_wealth_god = any(g in god_names for g in ["正财", "偏财"])
        wealth_stars = _palace_stars(star_positions, "财帛")
        result["summary"] = (f"In BaZi, {_el_disp(dm_element)} controls {_el_disp(wealth_element)} — that is your wealth element. "
                             f"Wealth stars are {'present' if has_wealth_god else 'not prominent'} among your ten gods, "
                             f"and your Wealth Palace holds {', '.join(_star_short(s) for s in wealth_stars) or 'no data'}.")
        result["key_points"] = [
            ("Wealth stars appear among your ten gods: you have a strong nose for money and for chances to make it" if has_wealth_god else "Wealth stars do not stand out among your ten gods: your money is more likely to grow through your career and long-term asset building than through opportunistic income"),
            (f"Strength: {strength_en} — " + ("you can carry wealth: active business-building and investing suit you" if strength == "强" else "your capacity to carry big money is limited — be careful with heavy leverage and high-volatility bets") if strength else ""),
            (f"Your Wealth Palace holds {', '.join(_star_disp(s) for s in wealth_stars)}: " + "; ".join(_STAR_TRAIT[s] for s in wealth_stars if s in _STAR_TRAIT)) if wealth_stars else "Wealth Palace major-star data was not provided",
        ]
        result["suggestions"] = [
            "Build stable cash flow first — predictable income and an emergency fund — before reaching for growth-style allocations; set the split by your real finances, not by mood",
            "When a 'fast money' chance shows up, sleep on it and write the downside down in numbers before you move",
        ]
    elif analysis_type == "relationship":
        spouse_god = ("the wealth stars (财星): Steady Wealth (正财) and Windfall Wealth (偏财)"
                      if gender == 1 else
                      "the authority stars (官杀): the Authority Star (正官) and the Pressure Star (七杀)")
        day_branch = (bazi.get("day_pillar") or "")[1:2]
        day_branch_disp = f"{_CT_BRANCH_PINYIN.get(day_branch, day_branch)} ({day_branch})" if day_branch else ""
        spouse_stars = _palace_stars(star_positions, "夫妻")
        result["summary"] = (f"Love reads from your day branch and your spouse stars: day branch {day_branch_disp or 'no data'}, "
                             f"and the Spouse Palace holds {', '.join(_star_short(s) for s in spouse_stars) or 'no data'}.")
        result["key_points"] = [
            f"Your day branch (your personal spouse palace) is {day_branch_disp} — the everyday flavor of how you do closeness" if day_branch else "Day branch data was not provided",
            f"Your spouse stars are {spouse_god} — how they sit in your chart shapes how you take the lead and how much you invest in a relationship",
            (f"Your Spouse Palace holds {', '.join(_star_disp(s) for s in spouse_stars)}: " + "; ".join(_STAR_TRAIT[s] for s in spouse_stars if s in _STAR_TRAIT)) if spouse_stars else "Spouse Palace major-star data was not provided",
        ]
        result["suggestions"] = [
            "Relationship quality depends far more on communication and boundaries — the chart only points to tendencies; it never names a specific person",
            "When the same argument or the same type keeps repeating, treat the pattern as the thing to work on, not the person in front of you",
        ]
    elif analysis_type == "health":
        health_stars = _palace_stars(star_positions, "疾厄")
        result["summary"] = f"Your weakest element is {_el_disp(weakest)}, which maps to {_ELEMENT_ORGAN.get(weakest, '')} — that is the system to look after first."
        result["key_points"] = [
            f"Element counts: {', '.join(f'{_CT_ELEMENT_EN.get(k, k)} {v}' for k, v in elements.items())} — {_el_disp(weakest)} is the weakest and {_el_disp(strongest)} the strongest",
            f"{_el_disp(weakest)} maps to {_ELEMENT_ORGAN.get(weakest, '')}: give that system first call on your sleep, food and rest",
            (f"Your Health Palace holds {', '.join(_star_short(s) for s in health_stars)} — a pointer to body tendencies, not a named illness") if health_stars else "Health Palace major-star data was not provided",
        ]
        result["suggestions"] = [
            "Keep sleep and movement regular; if a symptom sticks around for more than a couple of weeks, get it checked by a doctor instead of pushing through",
            f"Build one small daily habit that feeds your {_el_disp(weakest)} side — fixed sleep times and a daylight walk are a good start — and keep it for a full month before judging it",
        ]
    else:  # comprehensive 及其他类型：给三盘合参的规则摘要
        result["summary"] = "All three charts, one reading (rule-based): BaZi sets the structure, Zi Wei reads the life areas, Vedic sets the rising-sign tone."
        result["key_points"] = [
            f"BaZi: Day Master {dm_disp}, rated {strength_en or 'unrated'}; strongest element {_el_disp(strongest)}, weakest {_el_disp(weakest)}",
            star_line or "Zi Wei Life Palace data was not provided",
            f"Vedic rising sign {asc_sign}: your life stage and outer style carry this sign's flavor" if asc_sign else "Vedic rising sign was not provided",
            f"Ten-god layout: {', '.join(f'{_CT_STEM_POSITION_EN.get(k, k)} — {_god_disp(v)}' for k, v in ten_gods.items())}" if ten_gods else "Ten-god data was not provided",
        ]
        result["suggestions"] = [
            "Personality, career, wealth, love and health can each be opened up in depth in the full report",
            "This is the quick reading; for the fuller reasoning, see the complete paid report",
        ]

    # ---- 三盘补厚：紫微四化/宫位与吠陀行星落宫，按类型并入要点 ----
    extra = []
    if analysis_type == "personality":
        fude_stars = _palace_stars(star_positions, "福德")
        if fude_stars:
            extra.append(f"Your Fortune Palace (福德宫) holds {', '.join(_star_disp(x) for x in fude_stars)} — your inner world and what recharges you: {'; '.join(_STAR_TRAIT[x] for x in fude_stars if x in _STAR_TRAIT)}")
        if moon_sign:
            extra.append(f"Your Vedic Moon is in {moon_sign}: {_SIGN_TRAIT_V.get(moon_sign, '')} — this is your emotional base color and where your sense of safety comes from")
        if asc_lord and isinstance(asc_lord_house, int):
            extra.append(f"Your rising-sign lord, {_PLANET_EN.get(asc_lord, asc_lord)}, sits in house {asc_lord_house} ({_HOUSE_DOMAIN_V.get(asc_lord_house, '')}): your life naturally centers on this area")
    elif analysis_type == "career":
        t = _trans_in("官禄")
        if t:
            extra.append(f"Your Career Palace carries a birth-year transformation — {' and '.join(t)}: career is one of the places your birth-year charges land directly, which makes it a natural place to push")
        hl = _house_line(10)
        if hl:
            extra.append("Vedic: " + hl)
    elif analysis_type == "wealth":
        lu = _trans_line("禄")
        if lu:
            extra.append("Zi Wei: " + lu)
        lucun_palace = all_star_positions.get("禄存", "")
        if lucun_palace:
            extra.append(f"Lu Cun (禄存) · the Savings Star sits in the {_palace_disp(lucun_palace)} ({_PALACE_DOMAIN.get(lucun_palace, lucun_palace)}): this area carries a built-in, steady stream of income")
        hl = _house_line(2)
        if hl:
            extra.append("Vedic: " + hl)
    elif analysis_type == "relationship":
        t_pairs = _trans_in_pairs("夫妻")
        if t_pairs:
            t = [f"{_star_short(star)} carrying {_CT_SIHUA_EN.get(tt, tt)}" for star, tt in t_pairs]
            if any(tt == "忌" for _, tt in t_pairs):
                extra.append(f"Your Spouse Palace carries {' and '.join(t)}: with the Ji (忌) charge landing in love, you tend to hold on tight and need clear, explicit reassurance to feel safe")
            else:
                extra.append(f"Your Spouse Palace carries {' and '.join(t)}: love is one of the areas your birth-year charges mark as a priority zone")
        venus = planets_v.get("Venus") or {}
        if isinstance(venus, dict) and venus.get("sign"):
            extra.append(f"Your Vedic Venus is in {venus['sign']}, house {venus.get('house', '?')}: your taste and your way of falling for someone — in love, you especially value {_HOUSE_DOMAIN_V.get(venus.get('house'), 'the quality of the connection') if isinstance(venus.get('house'), int) else 'the quality of the connection'}")
        hl = _house_line(7)
        if hl:
            extra.append("Vedic: " + hl)
    elif analysis_type == "health":
        if moon_sign:
            extra.append(f"Your Vedic Moon is in {moon_sign}: your feelings and sleep rhythm are the barometer of your health — when things feel off, steady your routine and your mood first")
        hl = _house_line(6)
        if hl:
            extra.append("Vedic: " + hl)
    else:  # comprehensive
        if soul_star or body_star:
            extra.append(f"Zi Wei life lord {_star_short(soul_star) if soul_star else 'not provided'}, body lord {_star_short(body_star) if body_star else 'not provided'}: your inborn main tone and where you put in effort later in life")
        for ttype in ("禄", "忌"):
            tl = _trans_line(ttype)
            if tl:
                extra.append("Transformations: " + tl)
        if houses_v:
            busiest = max(houses_v, key=lambda h: len(houses_v[h]))
            if len(houses_v[busiest]) >= 2:
                extra.append("Vedic: " + _house_line(busiest))
        if moon_sign:
            extra.append(f"Your Vedic Moon is in {moon_sign}: {_SIGN_TRAIT_V.get(moon_sign, '')}")
    # ---- 第二层补厚：八字大运/喜用/神煞 + 吠陀尊贵/宫主/Dasha ----
    extra2 = []
    dayun_line = ""
    if current_dayun:
        gz, a0, a1 = current_dayun
        gz_el = _GAN_ELEMENT.get(gz[0], "")
        dayun_line = (f"Your current ten-year cycle is {_ct_pillar_pair(gz)} (ages {a0}–{a1}): its energy is {_el_disp(gz_el)}, "
                      f"so this decade keeps bringing {_ELEMENT_THEME.get(gz_el, '')} themes to the front")
    dasha_line = ""
    if dasha:
        nak_name, dlord, y0, y1 = dasha
        dasha_line = f"Your current Vedic period is the {_DASHA_EN.get(dlord, dlord)} period ({y0}–{y1}): {_DASHA_DOMAIN.get(dlord, 'this planet\u2019s themes')} is the main theme of these years"
    if analysis_type == "personality":
        if dasha:
            extra2.append(f"Your birth star (nakshatra) is {dasha[0]}, ruled by {_DASHA_EN.get(_NAKSHATRAS[[n for n, _ in _NAKSHATRAS].index(dasha[0])][1], '')}: it sets the deep grain of your temperament")
        extra2.extend([text for kind, text in dignity_lines if kind in ("exalted", "own")][:2])
    elif analysis_type == "career":
        if dayun_line:
            extra2.append(dayun_line + "; when picking a track, line up this decade's element themes with your supportive directions — going with the current costs far less effort than fighting it")
        hl = _house_lord_line(10)
        if hl:
            extra2.append("Vedic: " + hl)
    elif analysis_type == "wealth":
        if xi_yong:
            extra2.append("BaZi support directions: " + xi_yong + " — use it as one more weight on the scale when you choose")
        if dayun_line:
            extra2.append(dayun_line)
        if dasha_line:
            extra2.append(dasha_line)
    elif analysis_type == "relationship":
        hl = _house_lord_line(7)
        if hl:
            extra2.append("Vedic: " + hl)
        if dayun_line:
            extra2.append(dayun_line)
    elif analysis_type == "health":
        extra2.extend([text for kind, text in dignity_lines if kind == "debilitated"][:2])
        if dayun_line:
            extra2.append(dayun_line + "; the stretch around a cycle change is when your body tends to wobble — guard your routine then")
    else:  # comprehensive
        if spirits:
            extra2.append("Signature markers: " + "; ".join(_SPIRIT_GLOSS_EN.get(sp, sp) for sp in spirits[:3]))
        if dayun_line:
            extra2.append(dayun_line)
        if dasha_line:
            extra2.append(dasha_line)
        extra2.extend([text for _, text in dignity_lines[:2]])
    result["key_points"].extend([e for e in extra2 if e])
    extra3 = []
    body_line = ""
    if body_palace_name:
        bs = _major_stars_of(body_palace_name) or _palace_stars(star_positions, body_palace_name)
        body_line = (f"Your Body Palace sits in the {_palace_disp(body_palace_name)} ({_PALACE_DOMAIN.get(body_palace_name, body_palace_name)})"
                     + (f", holding {', '.join(_star_short(s) for s in bs)}" if bs else "")
                     + ": where your focus and your identity settle after midlife")
    trine_line = ""
    if trine_palaces:
        tstars = []
        for p in trine_palaces[1:]:
            tstars.extend(_major_stars_of(p) or _palace_stars(star_positions, p))
        if tstars:
            trine_line = (f"The other two corners of your life triangle (the Wealth and Career Palaces) send these stars into the mix: "
                          f"{', '.join(_star_short(s) for s in dict.fromkeys(tstars))} — money and work stay closely tied to your core self")
    if analysis_type == "personality":
        if body_line:
            extra3.append(body_line)
        bn = _brightness_note("命宫")
        if bn:
            extra3.append(f"Life Palace star brightness: {bn} (Peak/Strong means full power, expressed directly; Fallen means power held inward, needing time and practice to switch on)")
        if trine_line:
            extra3.append(trine_line)
    elif analysis_type == "career":
        fl = _fly_line("官禄")
        if fl:
            extra3.append("Flying stars: " + fl)
    elif analysis_type == "wealth":
        fl = _fly_line("财帛")
        if fl:
            extra3.append("Flying stars: " + fl)
    elif analysis_type == "relationship":
        fl = _fly_line("夫妻")
        if fl:
            extra3.append("Flying stars: " + fl)
        if body_line and body_palace_name == "夫妻":
            extra3.append(body_line + " (your Body Palace lands right in the Spouse Palace, so the state of your love life colors everything else more than usual)")
    elif analysis_type == "health":
        bn = _brightness_note("疾厄")
        if bn:
            extra3.append(f"Health Palace star brightness: {bn}")
    else:  # comprehensive
        _shown = [p for p in patterns if p[2] != "caution"][:2]
        _caution = [p for p in patterns if p[2] == "caution"]
        if _caution and len(_shown) < 3:
            _shown.append(_caution[0])
        for pname_, pdesc, _lvl in _shown:
            extra3.append(f"Pattern — {pname_}: {pdesc}")
        if body_line:
            extra3.append(body_line)
        fl = _fly_line("命宫")
        if fl:
            extra3.append("Flying stars: " + fl)
        if trine_line:
            extra3.append(trine_line)
    result["key_points"].extend([e for e in extra3 if e])
    if patterns:
        basis.append("Patterns: " + ", ".join(p[0] for p in patterns[:3]))
    if body_palace_name:
        basis.append(f"Body Palace: {_palace_disp(body_palace_name)}")
    if current_dayun:
        basis.append(f"Current ten-year cycle: {_ct_pillar_pair(current_dayun[0])}")
    if dasha:
        basis.append(f"Nakshatra {dasha[0]} · {_DASHA_EN.get(dasha[1], dasha[1])} period {dasha[2]}–{dasha[3]}")

    result["key_points"].extend([e for e in extra if e])

    result["key_points"] = [p for p in result["key_points"] if p]
    return result

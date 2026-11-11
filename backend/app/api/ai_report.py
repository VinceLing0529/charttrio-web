from fastapi import APIRouter, Depends, HTTPException, Response
from core.ratelimit import rate_limit
from pydantic import BaseModel
from typing import Dict, Any, List
import json
import os
import uuid
import requests
import aiohttp
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import re

router = APIRouter()

# 配置Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# 配置DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# 配置存储目录
REPORTS_DIR = Path(__file__).resolve().parents[1] / "data" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# 导入prompt管理功能
from .prompt_admin import load_prompt_template

class AIReportRequest(BaseModel):
    user_data: Dict[str, Any]  # 包含input, bazi, ziwei, vedic的完整用户数据
    order_id: str = None

class AIReportResponse(BaseModel):
    order_id: str
    sections: List[Dict[str, Any]]
    generated_at: str

# 英文月份名（显式列表，不用 strftime %B，避免依赖服务器 locale）
_MONTH_NAMES_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

def get_next_12_months():
    """获取从下个月开始的12个月份列表（英文站口径："December 2026"）"""
    current_date = datetime.now()
    next_month = current_date.replace(day=1) + timedelta(days=32)
    next_month = next_month.replace(day=1)  # 确保是下个月的第一天

    months = []
    for i in range(12):
        month_date = next_month.replace(month=next_month.month + i if next_month.month + i <= 12 else next_month.month + i - 12)
        if next_month.month + i > 12:
            month_date = month_date.replace(year=next_month.year + 1)
        months.append(f"{_MONTH_NAMES_EN[month_date.month - 1]} {month_date.year}")

    return months, f"{_MONTH_NAMES_EN[current_date.month - 1]} {current_date.year}"

def generate_order_id():
    """生成订单号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"AI{timestamp}{unique_id}"

def save_report_to_storage(order_id: str, report_data: dict, user_data: dict):
    """将报告保存到存储"""
    try:
        report_file = REPORTS_DIR / f"{order_id}.json"
        storage_data = {
            "order_id": order_id,
            "user_data": user_data,
            "report_data": report_data,
            "created_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(storage_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 报告已保存: {report_file}")
        return True
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 保存报告失败: {str(e)}")
        return False

def load_report_from_storage(order_id: str):
    """从存储中加载报告"""
    try:
        report_file = REPORTS_DIR / f"{order_id}.json"
        if not report_file.exists():
            return None
        
        with open(report_file, 'r', encoding='utf-8') as f:
            storage_data = json.load(f)
        
        return storage_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 加载报告失败: {str(e)}")
        return None

def list_all_reports():
    """列出所有报告（现行目录格式 {order_id}/status.json + 旧扁平 {order_id}.json）"""
    reports = []
    seen = set()
    try:
        if REPORTS_DIR.exists():
            for order_dir in REPORTS_DIR.iterdir():
                if not order_dir.is_dir():
                    continue
                status_file = order_dir / "status.json"
                if not status_file.exists():
                    continue
                try:
                    with open(status_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    reports.append({
                        "order_id": order_dir.name,
                        "created_at": data.get("created_at"),
                        "status": data.get("status", "prompts_generated")
                    })
                    seen.add(order_dir.name)
                except Exception as e:
                    print(f"跳过损坏的订单目录 {order_dir}: {str(e)}")
        for report_file in REPORTS_DIR.glob("*.json"):
            if report_file.stem in seen:
                continue
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                reports.append({
                    "order_id": data.get("order_id"),
                    "created_at": data.get("created_at"),
                    "status": data.get("status", "completed")
                })
            except Exception as e:
                print(f"跳过损坏的文件 {report_file}: {str(e)}")

        return sorted(reports, key=lambda x: x["created_at"] or "", reverse=True)
    except Exception as e:
        print(f"❌ 列出报告失败: {str(e)}")
        return []

# def call_gemini_api(prompt_text, max_retries=3):
#     """直接调用Gemini API，支持重试机制 - 已弃用，请使用 call_deepseek_api"""
#     # 该函数已被 call_deepseek_api 替代
#     return call_deepseek_api(prompt_text, max_retries)

async def call_deepseek_api(prompt_text, max_retries=3, model="deepseek-chat", temperature=0.7):
    """异步调用DeepSeek API，支持重试机制"""
    if not DEEPSEEK_API_KEY:
        raise Exception("DeepSeek API Key未配置，请设置DEEPSEEK_API_KEY环境变量")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are the report writer for ChartTrio, a birth-chart reading service that cross-checks three traditional systems: BaZi (the Chinese Four Pillars), Zi Wei Dou Shu (Chinese star astrology), and Vedic astrology (Jyotish). Write in plain, everyday English at a middle-school reading level. Follow the structure, rules, and output format given in the user's prompt exactly, and output only the requested JSON, with no extra text before or after it."},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": temperature,
        "stream": False
    }
    
    for attempt in range(max_retries):
        try:
            timeout = aiohttp.ClientTimeout(total=180)  # 3分钟超时
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(DEEPSEEK_API_URL, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            return content
                        else:
                            raise Exception("API返回格式错误")
                    else:
                        error_text = await response.text()
                        raise Exception(f"API请求失败: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            print(f"DeepSeek API调用超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                raise Exception("API调用多次超时，请检查网络连接或稍后重试")
            continue
        except Exception as e:
            print(f"DeepSeek API调用错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                raise e
            continue

# ---------- 动态周期数据（大运/流年/大限/Dasha，全部由本命数据机械推导） ----------
_STEMS = "甲乙丙丁戊己庚辛壬癸"
_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
_STEM_ELEM = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
_STEM_YANG = set("甲丙戊庚壬")
_BRANCH_MAIN_STEM = {"子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊", "巳": "丙", "午": "丁", "未": "己", "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬"}
_ELEM_GEN = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_ELEM_CTL = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
_SIGN_OFFSET = {"Aries": 0, "Taurus": 30, "Gemini": 60, "Cancer": 90, "Leo": 120, "Virgo": 150, "Libra": 180, "Scorpio": 210, "Sagittarius": 240, "Capricorn": 270, "Aquarius": 300, "Pisces": 330}
_DASHA_ORDER = [("Ketu", "计都", 7), ("Venus", "金星", 20), ("Sun", "太阳", 6), ("Moon", "月亮", 10), ("Mars", "火星", 7), ("Rahu", "罗睺", 18), ("Jupiter", "木星", 16), ("Saturn", "土星", 19), ("Mercury", "水星", 17)]


def _ten_god(day_stem, stem):
    if day_stem not in _STEM_ELEM or stem not in _STEM_ELEM:
        return "未知"
    de, te = _STEM_ELEM[day_stem], _STEM_ELEM[stem]
    same = (day_stem in _STEM_YANG) == (stem in _STEM_YANG)
    if te == de:
        return "比肩" if same else "劫财"
    if _ELEM_GEN[te] == de:
        return "偏印" if same else "正印"
    if _ELEM_CTL[te] == de:
        return "七杀" if same else "正官"
    if _ELEM_GEN[de] == te:
        return "食神" if same else "伤官"
    return "偏财" if same else "正财"


def _step_pillar(pillar, steps):
    return _STEMS[(_STEMS.index(pillar[0]) + steps) % 10] + _BRANCHES[(_BRANCHES.index(pillar[1]) + steps) % 12]


def _year_ganzhi(year):
    return _STEMS[(year - 4) % 10] + _BRANCHES[(year - 4) % 12]


def _star_label(star):
    label = star.get("name", "")
    if star.get("brightness"):
        label += f"（{star['brightness']}）"
    if star.get("mutagen"):
        label += f"·化{star['mutagen']}"
    return label


def _four_trans_text(ziwei):
    trans = ziwei.get("year_four_trans") or ziwei.get("si_hua") or ziwei.get("four_transformations") or {}
    palaces = (ziwei.get("chart") or {}).get("palaces") or {}
    loc = {}
    for pname, pdata in palaces.items():
        for st in pdata.get("major_stars", []):
            if st.get("mutagen"):
                loc[st["name"]] = pname
    out = {}
    for key in ("禄", "权", "科", "忌"):
        star = trans.get(key)
        if not star:
            out[key] = "未知"
        elif star in loc:
            out[key] = f"{star}（落{loc[star]}宫）"
        else:
            out[key] = star
    return out


def _dynamic_cycles_text(user_data):
    from datetime import date, timedelta
    input_data = user_data.get("input", {})
    bazi = user_data.get("bazi", {})
    ziwei = user_data.get("ziwei", {})
    vedic = user_data.get("vedic", {})
    months, _cur_month = get_next_12_months()
    win_start_year = int(months[0].rsplit(" ", 1)[1])
    win_end_year = int(months[-1].rsplit(" ", 1)[1])
    birth_year = int(str(input_data.get("birth_date", "1990"))[:4])
    age_win = win_start_year - birth_year
    dm = bazi.get("day_master", "")
    lines = []
    # 八字大运
    try:
        dy = bazi.get("dayun", {}) or {}
        direction, qiyun = dy.get("direction"), dy.get("qiyun_age")
        month_pillar = bazi.get("month_pillar")
        if direction and qiyun is not None and month_pillar:
            sign = 1 if direction == "顺" else -1
            parts = []
            for k in range(5):
                pl = _step_pillar(month_pillar, sign * (k + 1))
                a0, a1 = qiyun + 10 * k, qiyun + 10 * k + 9
                seg = f"{pl}运（约{a0}–{a1}岁，天干{_ten_god(dm, pl[0])}、地支本气{_ten_god(dm, _BRANCH_MAIN_STEM[pl[1]])}）"
                if a0 <= age_win <= a1:
                    seg += "←当前大运"
                parts.append(seg)
            lines.append(f"八字大运（{direction}行，{qiyun}岁起运）：" + "；".join(parts))
    except Exception:
        pass
    # 流年
    try:
        fys = []
        for y in sorted({win_start_year, win_end_year}):
            gz = _year_ganzhi(y)
            fys.append(f"{y}年{gz}（天干{_ten_god(dm, gz[0])}、地支本气{_ten_god(dm, _BRANCH_MAIN_STEM[gz[1]])}）")
        lines.append("流年：" + "；".join(fys) + "（运势窗口跨此两年）")
    except Exception:
        pass
    # 紫微大限与流年命宫
    try:
        basic = ziwei.get("basic_info", {}) or {}
        fec = basic.get("five_elements_class", "")
        num_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}
        start = next((v for ch, v in num_map.items() if ch in fec), None)
        palaces = (ziwei.get("chart") or {}).get("palaces") or {}
        year_stem = (bazi.get("year_pillar") or "甲")[0]
        gender = input_data.get("gender", 1)
        yang_year = year_stem in _STEM_YANG
        forward = (yang_year and gender == 1) or ((not yang_year) and gender == 0)
        if start and palaces:
            ordered = sorted(palaces.items(), key=lambda kv: kv[1].get("index", 0))
            names = [n for n, _ in ordered]
            ming_rank = names.index("命宫")
            step = 1 if forward else -1
            cur_k = None
            for k in range(12):
                if start + 10 * k <= age_win <= start + 10 * k + 9:
                    cur_k = k
                    break
            if cur_k is not None:
                segs = []
                for k in (cur_k - 1, cur_k, cur_k + 1):
                    if k < 0:
                        continue
                    pname, pdata = ordered[(ming_rank + step * k) % 12]
                    stars = "、".join(s.get("name", "") for s in pdata.get("major_stars", [])) or "空宫"
                    tag = "←当前大限" if k == cur_k else ""
                    segs.append(f"{pname}宫（约{start + 10 * k}–{start + 10 * k + 9}岁，主星{stars}）{tag}")
                lines.append(f"紫微大限（{fec}，{start}岁起，{'顺' if forward else '逆'}行）：" + "；".join(segs))
            by_branch = {pd.get("earthly_branch"): n for n, pd in palaces.items()}
            fl = []
            for y in sorted({win_start_year, win_end_year}):
                br = _year_ganzhi(y)[1]
                if br in by_branch:
                    fl.append(f"{y}年流年命宫在{by_branch[br]}宫")
            if fl:
                lines.append("紫微流年：" + "；".join(fl))
    except Exception:
        pass
    # Vedic Vimshottari
    try:
        moon = (vedic.get("planets") or {}).get("Moon", {})
        abs_lon = _SIGN_OFFSET[moon["sign"]] + float(moon["lon"])
        bd = date.fromisoformat(str(input_data.get("birth_date")))
        seg = 40.0 / 3.0
        idx = int(abs_lon // seg)
        lord_i = idx % 9
        frac = (abs_lon - idx * seg) / seg
        name, cn, yrs = _DASHA_ORDER[lord_i]
        timeline = [(name, cn, bd, bd + timedelta(days=(1 - frac) * yrs * 365.25))]
        i = lord_i
        while timeline[-1][3] < date(win_end_year, 12, 31):
            i = (i + 1) % 9
            n2, c2, y2 = _DASHA_ORDER[i]
            timeline.append((n2, c2, timeline[-1][3], timeline[-1][3] + timedelta(days=y2 * 365.25)))
        win_start = date(win_start_year, 12, 1)
        md = next(t for t in timeline if t[2] <= win_start < t[3])
        years_map = {n: y for n, _, y in _DASHA_ORDER}
        j = [n for n, _, _ in _DASHA_ORDER].index(md[0])
        ads = []
        ad_start = md[2]
        for k in range(9):
            n2, c2, y2 = _DASHA_ORDER[(j + k) % 9]
            ad_end = ad_start + timedelta(days=years_map[md[0]] * y2 / 120 * 365.25)
            ads.append((n2, c2, ad_start, ad_end))
            ad_start = ad_end
        ad = next(a for a in ads if a[2] <= win_start < a[3])
        ai = ads.index(ad)
        s = f"印度Vimshottari：当前{md[1]}大运（约{md[2].year}–{md[3].year}年），当前{ad[1]}小运（约{ad[2].year}–{ad[3].year}年）"
        if ai + 1 < 9 and ads[ai + 1][2] <= date(win_end_year, 11, 30):
            s += f"，{ads[ai + 1][2].year}年{ads[ai + 1][2].month}月前后转{ads[ai + 1][1]}小运"
        lines.append(s)
    except Exception:
        pass
    if not lines:
        return "动态周期数据不足，本节从略。"
    return "\n".join(lines)


def create_analysis_prompt(user_data: Dict[str, Any]) -> str:
    """创建优劣混合分析的prompt"""
    input_data = user_data.get('input', {})
    bazi = user_data.get('bazi', {})
    ziwei = user_data.get('ziwei', {})
    vedic = user_data.get('vedic', {})
    timezone_info = user_data.get('timezone_info', {})
    
    # 八字详细信息构建
    bazi_detail = ""
    if 'enhanced_analysis' in bazi:
        enhanced = bazi['enhanced_analysis']
        
        # 清理四柱详析中的空亡字段
        clean_columns = []
        for column in enhanced.get('四柱详析', []):
            clean_column = {k: v for k, v in column.items() if k != '空亡'}
            clean_columns.append(clean_column)
        
        bazi_detail = f"""
【八字详细分析】
四柱详析：{json.dumps(clean_columns, ensure_ascii=False)}
十神统计：{json.dumps(enhanced.get('十神统计', {}), ensure_ascii=False)}
五行分布：{json.dumps(enhanced.get('五行分布', {}), ensure_ascii=False)}
纳音：{json.dumps(bazi.get('nayin', {}), ensure_ascii=False)}
"""
    
    # 紫微斗数详细信息构建
    ziwei_lunar_date = "未知"
    ziwei_chinese_date = "未知"
    ziwei_soul = "未知"
    ziwei_body = "未知"
    ziwei_five_elements_class = "未知"
    ziwei_palaces_detail = "未知"
    ziwei_lu = "未知"
    ziwei_quan = "未知"
    ziwei_ke = "未知"
    ziwei_ji = "未知"
    
    if 'basic_info' in ziwei:
        basic_info = ziwei['basic_info']
        ziwei_lunar_date = basic_info.get('lunar_date', '未知')
        ziwei_chinese_date = basic_info.get('chinese_date', '未知')
        ziwei_soul = basic_info.get('soul', '未知')
        ziwei_body = basic_info.get('body', '未知')
        ziwei_five_elements_class = basic_info.get('five_elements_class', '未知')
    
    if 'chart' in ziwei and 'palaces' in ziwei['chart']:
        palaces = ziwei['chart']['palaces']
        ziwei_palaces_detail = ""
        for palace_name, palace_data in palaces.items():
            major_stars = [_star_label(star) for star in palace_data.get('major_stars', [])]
            minor_stars = palace_data.get('minor_stars', [])
            ziwei_palaces_detail += f"""
{palace_name}宫：{palace_data.get('heavenly_stem', '')}{palace_data.get('earthly_branch', '')}
- 主星：{', '.join(major_stars) if major_stars else '无'}
- 辅星：{', '.join(minor_stars) if minor_stars else '无'}
- 身宫：{'是' if palace_data.get('is_body_palace') else '否'}"""
    
    # 四化信息（引擎字段为 year_four_trans，附落宫）
    _ft = _four_trans_text(ziwei)
    ziwei_lu = _ft['禄']
    ziwei_quan = _ft['权']
    ziwei_ke = _ft['科']
    ziwei_ji = _ft['忌']
    
    # 印度星盘详细信息构建
    vedic_chart_type = vedic.get('chart_type', '未知')
    vedic_ayanamsa_type = vedic.get('ayanamsa', {}).get('type', '未知')
    vedic_ayanamsa_value = vedic.get('ayanamsa', {}).get('value', '未知')
    vedic_ascendant_sign = vedic.get('ascendant', {}).get('sign', '未知')
    vedic_ascendant_lon = vedic.get('ascendant', {}).get('lon', '未知')
    
    vedic_planets_detail = ""
    if 'planets' in vedic:
        for planet_name, planet_data in vedic['planets'].items():
            vedic_planets_detail += f"""
{planet_name}：{planet_data.get('sign', '未知')}座 第{planet_data.get('house', '未知')}宫 {planet_data.get('lon', '未知')}°"""
    
    vedic_axis_points_detail = ""
    if 'axis_points' in vedic:
        for axis_name, axis_data in vedic['axis_points'].items():
            vedic_axis_points_detail += f"""
{axis_name}：{axis_data.get('sign', '未知')}座 第{axis_data.get('house', '未知')}宫 {axis_data.get('lon', '未知')}°"""
    
    # 加载prompt模板
    dynamic_cycles = _dynamic_cycles_text(user_data)
    prompt_template = load_prompt_template("analysis")
    if not prompt_template:
        raise ValueError("无法加载analysis prompt模板")
    
    # 准备模板变量
    template_vars = {
        'gender_str': input_data.get('gender_str', '未知'),
        'birth_date': input_data.get('birth_date', ''),
        'birth_time': input_data.get('birth_time', ''),
        'true_solar_time': json.dumps(input_data.get('true_solar_time', {}), ensure_ascii=False),
        'location_name': input_data.get('location_name', '未知'),
        'longitude': input_data.get('longitude', '未知'),
        'latitude': input_data.get('latitude', '未知'),
        'timezone': timezone_info.get('timezone', '未知'),
        'bazi_year_pillar': bazi.get('year_pillar', '未知'),
        'bazi_month_pillar': bazi.get('month_pillar', '未知'),
        'bazi_day_pillar': bazi.get('day_pillar', '未知'),
        'bazi_hour_pillar': bazi.get('hour_pillar', '未知'),
        'bazi_day_master': bazi.get('day_master', '未知'),
        'bazi_body_strength': bazi.get('body_strength', '未知'),
        'bazi_five_elements': json.dumps(bazi.get('five_elements_count', {}), ensure_ascii=False),
        'bazi_ten_gods': json.dumps(bazi.get('ten_gods', {}), ensure_ascii=False),
        'bazi_enhanced_analysis': bazi_detail,
        'ziwei_lunar_date': ziwei_lunar_date,
        'ziwei_chinese_date': ziwei_chinese_date,
        'ziwei_soul': ziwei_soul,
        'ziwei_body': ziwei_body,
        'ziwei_five_elements_class': ziwei_five_elements_class,
        'ziwei_palaces_detail': ziwei_palaces_detail,
        'ziwei_lu': ziwei_lu,
        'ziwei_quan': ziwei_quan,
        'ziwei_ke': ziwei_ke,
        'ziwei_ji': ziwei_ji,
        'vedic_chart_type': vedic_chart_type,
        'vedic_ayanamsa_type': vedic_ayanamsa_type,
        'vedic_ayanamsa_value': vedic_ayanamsa_value,
        'vedic_ascendant_sign': vedic_ascendant_sign,
        'vedic_ascendant_lon': vedic_ascendant_lon,
        'vedic_planets_detail': vedic_planets_detail,
        'vedic_axis_points_detail': vedic_axis_points_detail,
        'dynamic_cycles': dynamic_cycles
    }
    
    # 格式化prompt
    try:
        formatted_prompt = prompt_template["content"].format(**template_vars)
        return formatted_prompt
    except KeyError as e:
        raise ValueError(f"Prompt模板格式化失败，缺少变量: {e}")

def create_mindmap_prompt(user_data: Dict[str, Any]) -> str:
    """创建思维导图呈现的prompt"""
    input_data = user_data.get('input', {})
    bazi = user_data.get('bazi', {})
    ziwei = user_data.get('ziwei', {})
    vedic = user_data.get('vedic', {})
    timezone_info = user_data.get('timezone_info', {})
    
    # 八字详细信息构建
    bazi_detail = ""
    if 'enhanced_analysis' in bazi:
        enhanced = bazi['enhanced_analysis']
        
        # 清理四柱详析中的空亡字段
        clean_columns = []
        for column in enhanced.get('四柱详析', []):
            clean_column = {k: v for k, v in column.items() if k != '空亡'}
            clean_columns.append(clean_column)
        
        bazi_detail = f"""
【八字详细分析】
四柱详析：{json.dumps(clean_columns, ensure_ascii=False)}
十神统计：{json.dumps(enhanced.get('十神统计', {}), ensure_ascii=False)}
五行分布：{json.dumps(enhanced.get('五行分布', {}), ensure_ascii=False)}
纳音：{json.dumps(bazi.get('nayin', {}), ensure_ascii=False)}
"""
    
    # 紫微斗数详细信息构建
    ziwei_lunar_date = "未知"
    ziwei_chinese_date = "未知"
    ziwei_soul = "未知"
    ziwei_body = "未知"
    ziwei_five_elements_class = "未知"
    ziwei_palaces_detail = "未知"
    ziwei_lu = "未知"
    ziwei_quan = "未知"
    ziwei_ke = "未知"
    ziwei_ji = "未知"
    
    if 'basic_info' in ziwei:
        basic_info = ziwei['basic_info']
        ziwei_lunar_date = basic_info.get('lunar_date', '未知')
        ziwei_chinese_date = basic_info.get('chinese_date', '未知')
        ziwei_soul = basic_info.get('soul', '未知')
        ziwei_body = basic_info.get('body', '未知')
        ziwei_five_elements_class = basic_info.get('five_elements_class', '未知')
    
    if 'chart' in ziwei and 'palaces' in ziwei['chart']:
        palaces = ziwei['chart']['palaces']
        ziwei_palaces_detail = ""
        for palace_name, palace_data in palaces.items():
            major_stars = [_star_label(star) for star in palace_data.get('major_stars', [])]
            minor_stars = palace_data.get('minor_stars', [])
            ziwei_palaces_detail += f"""
{palace_name}宫：{palace_data.get('heavenly_stem', '')}{palace_data.get('earthly_branch', '')}
- 主星：{', '.join(major_stars) if major_stars else '无'}
- 辅星：{', '.join(minor_stars) if minor_stars else '无'}
- 身宫：{'是' if palace_data.get('is_body_palace') else '否'}"""
    
    # 四化信息（引擎字段为 year_four_trans，附落宫）
    _ft = _four_trans_text(ziwei)
    ziwei_lu = _ft['禄']
    ziwei_quan = _ft['权']
    ziwei_ke = _ft['科']
    ziwei_ji = _ft['忌']
    
    # 印度星盘详细信息构建
    vedic_chart_type = vedic.get('chart_type', '未知')
    vedic_ayanamsa_type = vedic.get('ayanamsa', {}).get('type', '未知')
    vedic_ayanamsa_value = vedic.get('ayanamsa', {}).get('value', '未知')
    vedic_ascendant_sign = vedic.get('ascendant', {}).get('sign', '未知')
    vedic_ascendant_lon = vedic.get('ascendant', {}).get('lon', '未知')
    
    vedic_planets_detail = ""
    if 'planets' in vedic:
        for planet_name, planet_data in vedic['planets'].items():
            vedic_planets_detail += f"""
{planet_name}：{planet_data.get('sign', '未知')}座 第{planet_data.get('house', '未知')}宫 {planet_data.get('lon', '未知')}°"""
    
    vedic_axis_points_detail = ""
    if 'axis_points' in vedic:
        for axis_name, axis_data in vedic['axis_points'].items():
            vedic_axis_points_detail += f"""
{axis_name}：{axis_data.get('sign', '未知')}座 第{axis_data.get('house', '未知')}宫 {axis_data.get('lon', '未知')}°"""
    
    # 加载prompt模板
    dynamic_cycles = _dynamic_cycles_text(user_data)
    prompt_template = load_prompt_template("mindmap")
    if not prompt_template:
        raise ValueError("无法加载mindmap prompt模板")
    
    # 准备模板变量
    template_vars = {
        'gender_str': input_data.get('gender_str', '未知'),
        'birth_date': input_data.get('birth_date', ''),
        'birth_time': input_data.get('birth_time', ''),
        'true_solar_time': json.dumps(input_data.get('true_solar_time', {}), ensure_ascii=False),
        'location_name': input_data.get('location_name', '未知'),
        'longitude': input_data.get('longitude', '未知'),
        'latitude': input_data.get('latitude', '未知'),
        'timezone': timezone_info.get('timezone', '未知'),
        'bazi_year_pillar': bazi.get('year_pillar', '未知'),
        'bazi_month_pillar': bazi.get('month_pillar', '未知'),
        'bazi_day_pillar': bazi.get('day_pillar', '未知'),
        'bazi_hour_pillar': bazi.get('hour_pillar', '未知'),
        'bazi_day_master': bazi.get('day_master', '未知'),
        'bazi_body_strength': bazi.get('body_strength', '未知'),
        'bazi_five_elements': json.dumps(bazi.get('five_elements_count', {}), ensure_ascii=False),
        'bazi_ten_gods': json.dumps(bazi.get('ten_gods', {}), ensure_ascii=False),
        'bazi_enhanced_analysis': bazi_detail,
        'ziwei_lunar_date': ziwei_lunar_date,
        'ziwei_chinese_date': ziwei_chinese_date,
        'ziwei_soul': ziwei_soul,
        'ziwei_body': ziwei_body,
        'ziwei_five_elements_class': ziwei_five_elements_class,
        'ziwei_palaces_detail': ziwei_palaces_detail,
        'ziwei_lu': ziwei_lu,
        'ziwei_quan': ziwei_quan,
        'ziwei_ke': ziwei_ke,
        'ziwei_ji': ziwei_ji,
        'vedic_chart_type': vedic_chart_type,
        'vedic_ayanamsa_type': vedic_ayanamsa_type,
        'vedic_ayanamsa_value': vedic_ayanamsa_value,
        'vedic_ascendant_sign': vedic_ascendant_sign,
        'vedic_ascendant_lon': vedic_ascendant_lon,
        'vedic_planets_detail': vedic_planets_detail,
        'vedic_axis_points_detail': vedic_axis_points_detail,
        'dynamic_cycles': dynamic_cycles
    }
    
    # 格式化prompt
    try:
        formatted_prompt = prompt_template["content"].format(**template_vars)
        return formatted_prompt
    except KeyError as e:
        raise ValueError(f"Prompt模板格式化失败，缺少变量: {e}")

def create_fortune_prompt(user_data: Dict[str, Any]) -> str:
    """创建运势预测报告的prompt"""
    input_data = user_data.get('input', {})
    bazi = user_data.get('bazi', {})
    ziwei = user_data.get('ziwei', {})
    vedic = user_data.get('vedic', {})
    timezone_info = user_data.get('timezone_info', {})
    
    # 获取预测月份信息
    prediction_months, current_month = get_next_12_months()
    
    # 八字详细信息构建
    bazi_detail = ""
    if 'enhanced_analysis' in bazi:
        enhanced = bazi['enhanced_analysis']
        
        # 清理四柱详析中的空亡字段
        clean_columns = []
        for column in enhanced.get('四柱详析', []):
            clean_column = {k: v for k, v in column.items() if k != '空亡'}
            clean_columns.append(clean_column)
        
        bazi_detail = f"""
【八字详细分析】
四柱详析：{json.dumps(clean_columns, ensure_ascii=False)}
十神统计：{json.dumps(enhanced.get('十神统计', {}), ensure_ascii=False)}
五行分布：{json.dumps(enhanced.get('五行分布', {}), ensure_ascii=False)}
纳音：{json.dumps(bazi.get('nayin', {}), ensure_ascii=False)}
"""
    
    # 紫微斗数详细信息构建
    ziwei_lunar_date = "未知"
    ziwei_chinese_date = "未知"
    ziwei_soul = "未知"
    ziwei_body = "未知"
    ziwei_five_elements_class = "未知"
    ziwei_palaces_detail = "未知"
    ziwei_lu = "未知"
    ziwei_quan = "未知"
    ziwei_ke = "未知"
    ziwei_ji = "未知"
    
    if 'basic_info' in ziwei:
        basic_info = ziwei['basic_info']
        ziwei_lunar_date = basic_info.get('lunar_date', '未知')
        ziwei_chinese_date = basic_info.get('chinese_date', '未知')
        ziwei_soul = basic_info.get('soul', '未知')
        ziwei_body = basic_info.get('body', '未知')
        ziwei_five_elements_class = basic_info.get('five_elements_class', '未知')
    
    if 'chart' in ziwei and 'palaces' in ziwei['chart']:
        palaces = ziwei['chart']['palaces']
        ziwei_palaces_detail = ""
        for palace_name, palace_data in palaces.items():
            major_stars = [_star_label(star) for star in palace_data.get('major_stars', [])]
            minor_stars = palace_data.get('minor_stars', [])
            ziwei_palaces_detail += f"""
{palace_name}宫：{palace_data.get('heavenly_stem', '')}{palace_data.get('earthly_branch', '')}
- 主星：{', '.join(major_stars) if major_stars else '无'}
- 辅星：{', '.join(minor_stars) if minor_stars else '无'}
- 身宫：{'是' if palace_data.get('is_body_palace') else '否'}"""
    
    # 四化信息（引擎字段为 year_four_trans，附落宫）
    _ft = _four_trans_text(ziwei)
    ziwei_lu = _ft['禄']
    ziwei_quan = _ft['权']
    ziwei_ke = _ft['科']
    ziwei_ji = _ft['忌']
    
    # 印度星盘详细信息构建
    vedic_chart_type = vedic.get('chart_type', '未知')
    vedic_ayanamsa_type = vedic.get('ayanamsa', {}).get('type', '未知')
    vedic_ayanamsa_value = vedic.get('ayanamsa', {}).get('value', '未知')
    vedic_ascendant_sign = vedic.get('ascendant', {}).get('sign', '未知')
    vedic_ascendant_lon = vedic.get('ascendant', {}).get('lon', '未知')
    
    vedic_planets_detail = ""
    if 'planets' in vedic:
        for planet_name, planet_data in vedic['planets'].items():
            vedic_planets_detail += f"""
{planet_name}：{planet_data.get('sign', '未知')}座 第{planet_data.get('house', '未知')}宫 {planet_data.get('lon', '未知')}°"""
    
    vedic_axis_points_detail = ""
    if 'axis_points' in vedic:
        for axis_name, axis_data in vedic['axis_points'].items():
            vedic_axis_points_detail += f"""
{axis_name}：{axis_data.get('sign', '未知')}座 第{axis_data.get('house', '未知')}宫 {axis_data.get('lon', '未知')}°"""
    
    # 加载prompt模板
    dynamic_cycles = _dynamic_cycles_text(user_data)
    prompt_template = load_prompt_template("fortune")
    if not prompt_template:
        raise ValueError("无法加载fortune prompt模板")
    
    # 准备模板变量
    template_vars = {
        'gender_str': input_data.get('gender_str', '未知'),
        'birth_date': input_data.get('birth_date', ''),
        'birth_time': input_data.get('birth_time', ''),
        'true_solar_time': json.dumps(input_data.get('true_solar_time', {}), ensure_ascii=False),
        'location_name': input_data.get('location_name', '未知'),
        'longitude': input_data.get('longitude', '未知'),
        'latitude': input_data.get('latitude', '未知'),
        'timezone': timezone_info.get('timezone', '未知'),
        'bazi_year_pillar': bazi.get('year_pillar', '未知'),
        'bazi_month_pillar': bazi.get('month_pillar', '未知'),
        'bazi_day_pillar': bazi.get('day_pillar', '未知'),
        'bazi_hour_pillar': bazi.get('hour_pillar', '未知'),
        'bazi_day_master': bazi.get('day_master', '未知'),
        'bazi_body_strength': bazi.get('body_strength', '未知'),
        'bazi_five_elements': json.dumps(bazi.get('five_elements_count', {}), ensure_ascii=False),
        'bazi_ten_gods': json.dumps(bazi.get('ten_gods', {}), ensure_ascii=False),
        'bazi_enhanced_analysis': bazi_detail,
        'ziwei_lunar_date': ziwei_lunar_date,
        'ziwei_chinese_date': ziwei_chinese_date,
        'ziwei_soul': ziwei_soul,
        'ziwei_body': ziwei_body,
        'ziwei_five_elements_class': ziwei_five_elements_class,
        'ziwei_palaces_detail': ziwei_palaces_detail,
        'ziwei_lu': ziwei_lu,
        'ziwei_quan': ziwei_quan,
        'ziwei_ke': ziwei_ke,
        'ziwei_ji': ziwei_ji,
        'vedic_chart_type': vedic_chart_type,
        'vedic_ayanamsa_type': vedic_ayanamsa_type,
        'vedic_ayanamsa_value': vedic_ayanamsa_value,
        'vedic_ascendant_sign': vedic_ascendant_sign,
        'vedic_ascendant_lon': vedic_ascendant_lon,
        'vedic_planets_detail': vedic_planets_detail,
        'vedic_axis_points_detail': vedic_axis_points_detail,
        'dynamic_cycles': dynamic_cycles,
        'current_month': current_month,
        'prediction_start': prediction_months[0] if prediction_months else "未知",
        'prediction_end': prediction_months[-1] if prediction_months else "未知"
    }
    
    # 添加预测月份变量
    for i, month in enumerate(prediction_months):
        template_vars[f'prediction_month_{i}'] = month
    
    # 格式化prompt
    try:
        formatted_prompt = prompt_template["content"].format(**template_vars)
        return formatted_prompt
    except KeyError as e:
        raise ValueError(f"Prompt模板格式化失败，缺少变量: {e}")

def create_qa_prompt(user_data: Dict[str, Any]) -> str:
    """创建个性化建议的prompt"""
    input_data = user_data.get('input', {})
    bazi = user_data.get('bazi', {})
    ziwei = user_data.get('ziwei', {})
    vedic = user_data.get('vedic', {})
    timezone_info = user_data.get('timezone_info', {})
    
    # 八字详细信息构建
    bazi_detail = ""
    if 'enhanced_analysis' in bazi:
        enhanced = bazi['enhanced_analysis']
        
        # 清理四柱详析中的空亡字段
        clean_columns = []
        for column in enhanced.get('四柱详析', []):
            clean_column = {k: v for k, v in column.items() if k != '空亡'}
            clean_columns.append(clean_column)
        
        bazi_detail = f"""
【八字详细分析】
四柱详析：{json.dumps(clean_columns, ensure_ascii=False)}
十神统计：{json.dumps(enhanced.get('十神统计', {}), ensure_ascii=False)}
五行分布：{json.dumps(enhanced.get('五行分布', {}), ensure_ascii=False)}
纳音：{json.dumps(bazi.get('nayin', {}), ensure_ascii=False)}
"""
    
    # 紫微斗数详细信息构建
    ziwei_lunar_date = "未知"
    ziwei_chinese_date = "未知"
    ziwei_soul = "未知"
    ziwei_body = "未知"
    ziwei_five_elements_class = "未知"
    ziwei_palaces_detail = "未知"
    ziwei_lu = "未知"
    ziwei_quan = "未知"
    ziwei_ke = "未知"
    ziwei_ji = "未知"
    
    if 'basic_info' in ziwei:
        basic_info = ziwei['basic_info']
        ziwei_lunar_date = basic_info.get('lunar_date', '未知')
        ziwei_chinese_date = basic_info.get('chinese_date', '未知')
        ziwei_soul = basic_info.get('soul', '未知')
        ziwei_body = basic_info.get('body', '未知')
        ziwei_five_elements_class = basic_info.get('five_elements_class', '未知')
    
    if 'chart' in ziwei and 'palaces' in ziwei['chart']:
        palaces = ziwei['chart']['palaces']
        ziwei_palaces_detail = ""
        for palace_name, palace_data in palaces.items():
            major_stars = [_star_label(star) for star in palace_data.get('major_stars', [])]
            minor_stars = palace_data.get('minor_stars', [])
            ziwei_palaces_detail += f"""
{palace_name}宫：{palace_data.get('heavenly_stem', '')}{palace_data.get('earthly_branch', '')}
- 主星：{', '.join(major_stars) if major_stars else '无'}
- 辅星：{', '.join(minor_stars) if minor_stars else '无'}
- 身宫：{'是' if palace_data.get('is_body_palace') else '否'}"""
    
    # 四化信息（引擎字段为 year_four_trans，附落宫）
    _ft = _four_trans_text(ziwei)
    ziwei_lu = _ft['禄']
    ziwei_quan = _ft['权']
    ziwei_ke = _ft['科']
    ziwei_ji = _ft['忌']
    
    # 印度星盘详细信息构建
    vedic_chart_type = vedic.get('chart_type', '未知')
    vedic_ayanamsa_type = vedic.get('ayanamsa', {}).get('type', '未知')
    vedic_ayanamsa_value = vedic.get('ayanamsa', {}).get('value', '未知')
    vedic_ascendant_sign = vedic.get('ascendant', {}).get('sign', '未知')
    vedic_ascendant_lon = vedic.get('ascendant', {}).get('lon', '未知')
    
    vedic_planets_detail = ""
    if 'planets' in vedic:
        for planet_name, planet_data in vedic['planets'].items():
            vedic_planets_detail += f"""
{planet_name}：{planet_data.get('sign', '未知')}座 第{planet_data.get('house', '未知')}宫 {planet_data.get('lon', '未知')}°"""
    
    vedic_axis_points_detail = ""
    if 'axis_points' in vedic:
        for axis_name, axis_data in vedic['axis_points'].items():
            vedic_axis_points_detail += f"""
{axis_name}：{axis_data.get('sign', '未知')}座 第{axis_data.get('house', '未知')}宫 {axis_data.get('lon', '未知')}°"""
    
    # 加载prompt模板
    dynamic_cycles = _dynamic_cycles_text(user_data)
    prompt_template = load_prompt_template("qa")
    if not prompt_template:
        raise ValueError("无法加载qa prompt模板")
    
    # 准备模板变量
    template_vars = {
        'gender_str': input_data.get('gender_str', '未知'),
        'birth_date': input_data.get('birth_date', ''),
        'birth_time': input_data.get('birth_time', ''),
        'true_solar_time': json.dumps(input_data.get('true_solar_time', {}), ensure_ascii=False),
        'location_name': input_data.get('location_name', '未知'),
        'longitude': input_data.get('longitude', '未知'),
        'latitude': input_data.get('latitude', '未知'),
        'timezone': timezone_info.get('timezone', '未知'),
        'bazi_year_pillar': bazi.get('year_pillar', '未知'),
        'bazi_month_pillar': bazi.get('month_pillar', '未知'),
        'bazi_day_pillar': bazi.get('day_pillar', '未知'),
        'bazi_hour_pillar': bazi.get('hour_pillar', '未知'),
        'bazi_day_master': bazi.get('day_master', '未知'),
        'bazi_body_strength': bazi.get('body_strength', '未知'),
        'bazi_five_elements': json.dumps(bazi.get('five_elements_count', {}), ensure_ascii=False),
        'bazi_ten_gods': json.dumps(bazi.get('ten_gods', {}), ensure_ascii=False),
        'bazi_enhanced_analysis': bazi_detail,
        'ziwei_lunar_date': ziwei_lunar_date,
        'ziwei_chinese_date': ziwei_chinese_date,
        'ziwei_soul': ziwei_soul,
        'ziwei_body': ziwei_body,
        'ziwei_five_elements_class': ziwei_five_elements_class,
        'ziwei_palaces_detail': ziwei_palaces_detail,
        'ziwei_lu': ziwei_lu,
        'ziwei_quan': ziwei_quan,
        'ziwei_ke': ziwei_ke,
        'ziwei_ji': ziwei_ji,
        'vedic_chart_type': vedic_chart_type,
        'vedic_ayanamsa_type': vedic_ayanamsa_type,
        'vedic_ayanamsa_value': vedic_ayanamsa_value,
        'vedic_ascendant_sign': vedic_ascendant_sign,
        'vedic_ascendant_lon': vedic_ascendant_lon,
        'vedic_planets_detail': vedic_planets_detail,
        'vedic_axis_points_detail': vedic_axis_points_detail,
        'dynamic_cycles': dynamic_cycles
    }
    
    # 格式化prompt
    try:
        formatted_prompt = prompt_template["content"].format(**template_vars)
        return formatted_prompt
    except KeyError as e:
        raise ValueError(f"Prompt模板格式化失败，缺少变量: {e}")

def create_report_sections(bazi_analysis, ziwei_analysis, vedic_analysis, mindmap_data):
    """根据AI分析结果创建报告sections"""
    
    # 默认的section模板（与ExamplePage保持一致的格式）
    sections = [
        {
            "id": "analysis",
            "title": "优劣混合分析",
            "description": "结合三盘找出您的优势与劣势，深度剖析命理结构。",
            "icon": "📊",
            "gradient": "from-blue-500 to-cyan-500",
            "bgGradient": "from-blue-500/10 to-cyan-500/10",
            "borderGradient": "from-blue-500/50 to-cyan-500/50",
            "score": 88,
            "summary": bazi_analysis[:200] + "..." if len(bazi_analysis) > 200 else bazi_analysis,
            "detailSections": [
                {
                    "icon": "🎯",
                    "title": "八字综合分析",
                    "content": bazi_analysis,
                    "score": 85
                },
                {
                    "icon": "⭐",
                    "title": "紫微斗数解析",
                    "content": ziwei_analysis,
                    "score": 90
                },
                {
                    "icon": "🔯",
                    "title": "印度星盘洞察",
                    "content": vedic_analysis,
                    "score": 88
                }
            ]
        },
        {
            "id": "mindmap",
            "title": "思维导图呈现",
            "description": "用思维导图方式呈现命理构造与人生主线。",
            "icon": "⭐",
            "gradient": "from-amber-500 to-orange-500",
            "bgGradient": "from-amber-500/10 to-orange-500/10",
            "borderGradient": "from-amber-500/50 to-orange-500/50",
            "score": 92,
            "summary": "您的人生发展轨迹清晰，各个阶段都有明确的成长目标。",
            "mindMapData": mindmap_data,
            "detailSections": []
        },
        {
            "id": "fortune",
            "title": "运势预测报告",
            "description": "未来一年运势详细预测，助您把握人生机遇。",
            "icon": "🔮",
            "gradient": "from-purple-500 to-pink-500",
            "bgGradient": "from-purple-500/10 to-pink-500/10",
            "borderGradient": "from-purple-500/50 to-pink-500/50",
            "score": 85,
            "summary": "2024年下半年至2025年上半年整体运势上升，特别是事业和财运方面有明显改善。",
            "detailSections": [
                {
                    "icon": "💼",
                    "title": "事业运势分析",
                    "content": "基于您的命理配置，预测未来一年的事业发展趋势...",
                    "score": 88
                },
                {
                    "icon": "💎",
                    "title": "财运趋势预测",
                    "content": "分析您的财运变化规律和投资时机...",
                    "score": 82
                }
            ]
        },
        {
            "id": "suggestions",
            "title": "个性化建议",
            "description": "五维（性格、事业、财富、感情、成长）深度解答。",
            "icon": "💡",
            "gradient": "from-emerald-500 to-teal-500",
            "bgGradient": "from-emerald-500/10 to-teal-500/10",
            "borderGradient": "from-emerald-500/50 to-teal-500/50",
            "score": 90,
            "summary": "基于您的命理特点，提供全方位的人生发展建议和实用指导。",
            "detailSections": [
                {
                    "icon": "🎭",
                    "title": "性格优化建议",
                    "content": "根据八字分析提供的性格改善建议...",
                    "score": 88
                },
                {
                    "icon": "🚀",
                    "title": "事业发展建议",
                    "content": "基于紫微斗数的事业规划指导...",
                    "score": 92
                }
            ]
        }
    ]
    
    return sections

@router.post("/generate", response_model=AIReportResponse)
async def generate_ai_report(request: AIReportRequest):
    """生成AI报告 - 新流程：只生成prompt文件"""
    try:
        # 生成订单号
        order_id = request.order_id or generate_order_id()
        
        # 创建订单目录
        order_dir = REPORTS_DIR / order_id
        order_dir.mkdir(parents=True, exist_ok=True)
        
        # 提取用户数据
        user_data = request.user_data
        input_data = user_data.get('input', {})
        bazi_data = user_data.get('bazi', {})
        ziwei_data = user_data.get('ziwei', {})
        vedic_data = user_data.get('vedic', {})
        
        # 生成四个模块的prompt文件
        prompts = {
            "analysis": create_analysis_prompt(user_data),
            "mindmap": create_mindmap_prompt(user_data), 
            "fortune": create_fortune_prompt(user_data),
            "qa": create_qa_prompt(user_data)
        }
        
        # 保存prompt文件
        for module_name, prompt_content in prompts.items():
            prompt_file = order_dir / f"{module_name}_prompt.txt"
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt_content)
        
        # 创建初始状态文件
        status_data = {
            "order_id": order_id,
            "created_at": datetime.now().isoformat(),
            "status": "prompts_generated",
            "modules": {
                "analysis": {"status": "pending", "progress": 0},
                "mindmap": {"status": "pending", "progress": 0},
                "fortune": {"status": "pending", "progress": 0},
                "qa": {"status": "pending", "progress": 0}
            }
        }
        
        status_file = order_dir / "status.json"
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        
        # 保存用户数据
        user_data_file = order_dir / "user_data.json"
        with open(user_data_file, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Prompt文件已生成: {order_id}")
        
        return AIReportResponse(
            order_id=order_id,
            sections=[],  # 空数组，因为还没有生成内容
            generated_at=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 生成prompt文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成prompt文件失败: {str(e)}")

@router.get("/status/{order_id}")
async def get_report_status(order_id: str):
    """获取报告生成状态（现行目录格式优先，兼容旧扁平格式）"""
    try:
        order_dir = REPORTS_DIR / order_id
        status_file = order_dir / "status.json"
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
            modules = status_data.get("modules", {})
            total = len(modules)
            done = sum(1 for m in modules.values() if m.get("status") == "completed")
            progress = round(done / total * 100) if total else 0
            return {
                "order_id": order_id,
                "status": status_data.get("status", "prompts_generated"),
                "progress": progress,
                "created_at": status_data.get("created_at"),
                "report_available": done > 0
            }

        storage_data = load_report_from_storage(order_id)

        if not storage_data:
            raise HTTPException(status_code=404, detail=f"订单号 {order_id} 不存在")

        return {
            "order_id": order_id,
            "status": storage_data.get("status", "completed"),
            "progress": 100,
            "created_at": storage_data.get("created_at"),
            "report_available": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询订单状态失败: {str(e)}")

@router.get("/report/{order_id}")
async def get_report_by_order_id(order_id: str):
    """通过订单号获取完整报告"""
    try:
        order_dir = REPORTS_DIR / order_id
        if not order_dir.exists():
            raise HTTPException(status_code=404, detail=f"订单号 {order_id} 不存在")
        
        # 读取状态文件
        status_file = order_dir / "status.json"
        if not status_file.exists():
            raise HTTPException(status_code=404, detail="状态文件不存在")
        
        with open(status_file, 'r', encoding='utf-8') as f:
            status_data = json.load(f)
        
        # 读取用户数据
        user_data_file = order_dir / "user_data.json"
        user_data = {}
        if user_data_file.exists():
            with open(user_data_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
        
        # 读取所有已生成的模块数据
        sections = []
        modules = status_data.get("modules", {})
        
        for module_name, module_status in modules.items():
            if module_status.get("status") == "completed":
                result_file = order_dir / f"{module_name}_result.json"
                if result_file.exists():
                    with open(result_file, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                    sections.append({
                        "id": module_name,
                        "title": get_module_title(module_name),
                        "content": result_data.get("content", ""),
                        "generated_at": result_data.get("generated_at")
                    })
        
        return {
            "order_id": order_id,
            "sections": sections,
            "generated_at": status_data.get("created_at"),
            "status": status_data.get("status", "prompts_generated"),
            "user_data": user_data
        }
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告失败: {str(e)}")

def get_module_title(module_name):
    """获取模块标题"""
    titles = {
        "analysis": "优劣混合分析",
        "mindmap": "思维导图呈现", 
        "fortune": "运势预测报告",
        "qa": "个性化建议"
    }
    return titles.get(module_name, module_name)

@router.get("/reports/list")
async def list_reports():
    """列出所有报告"""
    try:
        reports = list_all_reports()
        return {"reports": reports}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告列表失败: {str(e)}")

# 新增API端点

class ModuleGenerateRequest(BaseModel):
    order_id: str
    module: str  # analysis, mindmap, fortune, qa

@router.post("/generate-module", dependencies=[Depends(rate_limit("gen-module", 10, 60))])
async def generate_single_module(request: ModuleGenerateRequest):
    """生成单个模块的报告"""
    if request.module not in {"analysis", "mindmap", "fortune", "qa"}:
        raise HTTPException(status_code=404, detail=f"模块不存在: {request.module}")
    try:
        order_dir = REPORTS_DIR / request.order_id
        if not order_dir.exists():
            raise HTTPException(status_code=404, detail="订单不存在")

        # 幂等闸：已生成过的模块直接回存量结果，绝不重复调用 AI 烧 token。
        # （前端重复点击、网络重试、恶意重放都只读盘，不产生新费用。）
        result_file = order_dir / f"{request.module}_result.json"
        if result_file.exists():
            return {
                "order_id": request.order_id,
                "module": request.module,
                "status": "completed",
                "message": "模块报告已存在，直接返回此前生成的结果",
                "cached": True,
            }
        
        # 读取prompt文件
        prompt_file = order_dir / f"{request.module}_prompt.txt"
        if not prompt_file.exists():
            raise HTTPException(status_code=404, detail="Prompt文件不存在")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # 调用AI生成内容
        print(f"🚀 开始生成模块 {request.module} 的报告...")
        ai_response = await call_deepseek_api(prompt_content)

        # 统一清洗content字段，去除```json ... ```包裹
        def clean_ai_content(content: str) -> str:
            content = content.strip()
            if content.startswith("```json"):
                content = re.sub(r"^```json\\s*", "", content)
                content = re.sub(r"\\s*```$", "", content)
            return content
        cleaned_content = clean_ai_content(ai_response)

        # 解析AI返回的JSON内容
        try:
            parsed_content = json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            print(f"⚠️ AI返回内容不是有效JSON，保存为字符串: {str(e)}")
            parsed_content = cleaned_content

        # 保存AI响应（result_file 已在上方幂等检查处定义）
        result_data = {
            "module": request.module,
            "order_id": request.order_id,
            "generated_at": datetime.now().isoformat(),
            "content": parsed_content
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        # 更新状态文件
        status_file = order_dir / "status.json"
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
            
            status_data["modules"][request.module] = {
                "status": "completed",
                "progress": 100,
                "completed_at": datetime.now().isoformat()
            }
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 模块 {request.module} 报告生成完成")
        
        return {
            "order_id": request.order_id,
            "module": request.module,
            "status": "completed",
            "message": "模块报告生成完成"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 生成模块报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成模块报告失败: {str(e)}")

@router.get("/module-status/{order_id}")
async def get_module_status(order_id: str):
    """获取订单中所有模块的状态"""
    try:
        order_dir = REPORTS_DIR / order_id
        if not order_dir.exists():
            raise HTTPException(status_code=404, detail="订单不存在")
        
        status_file = order_dir / "status.json"
        if not status_file.exists():
            raise HTTPException(status_code=404, detail="状态文件不存在")
        
        with open(status_file, 'r', encoding='utf-8') as f:
            status_data = json.load(f)
        
        return status_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模块状态失败: {str(e)}")

@router.get("/module-data/{order_id}/{module}")
async def get_module_data(order_id: str, module: str):
    """获取指定模块的数据"""
    try:
        order_dir = REPORTS_DIR / order_id
        if not order_dir.exists():
            raise HTTPException(status_code=404, detail="订单不存在")
        
        result_file = order_dir / f"{module}_result.json"
        if not result_file.exists():
            raise HTTPException(status_code=404, detail="模块数据不存在")
        
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        return result_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模块数据失败: {str(e)}")

@router.get("/snapshot/{order_id}")
async def get_snapshot_card(order_id: str):
    """命盘快照：把 analysis 的大白话内容渲染成一张可保存分享的 PNG 卡片（不调用 AI）。"""
    order_dir = REPORTS_DIR / order_id
    if not order_dir.exists():
        raise HTTPException(status_code=404, detail="订单不存在")
    result_file = order_dir / "analysis_result.json"
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="优劣分析尚未生成，暂时无法生成快照")

    with open(result_file, 'r', encoding='utf-8') as f:
        result_data = json.load(f)
    content = result_data.get("content")
    if isinstance(content, str):
        s = content.strip()
        s = re.sub(r"^```json\s*", "", s, flags=re.I)
        s = re.sub(r"^```\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
        try:
            content = json.loads(s)
        except Exception:
            raise HTTPException(status_code=500, detail="报告内容解析失败")
    if not isinstance(content, dict):
        raise HTTPException(status_code=500, detail="报告内容解析失败")

    # 延迟导入：缺 Pillow/字体时只影响本接口，不拖垮整个 API
    from .snapshot_card import render_snapshot_png, SnapshotFontError
    try:
        png = render_snapshot_png(content)
    except SnapshotFontError:
        raise HTTPException(status_code=503, detail="服务器字体未就绪，快照功能暂时不可用")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return Response(
        content=png,
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="snapshot-{order_id}.png"',
            "Cache-Control": "private, max-age=300",
        },
    )

@router.post("/simulate-progress/{order_id}/{module}")
async def simulate_progress(order_id: str, module: str):
    """模拟生成进度（用于前端显示）"""
    if module not in {"analysis", "mindmap", "fortune", "qa"}:
        raise HTTPException(status_code=404, detail=f"模块不存在: {module}")
    try:
        order_dir = REPORTS_DIR / order_id
        if not order_dir.exists():
            raise HTTPException(status_code=404, detail="订单不存在")
        
        status_file = order_dir / "status.json"
        if not status_file.exists():
            raise HTTPException(status_code=404, detail="状态文件不存在")
        
        # 读取当前状态
        with open(status_file, 'r', encoding='utf-8') as f:
            status_data = json.load(f)
        
        # 更新模块状态为生成中
        status_data["modules"][module] = {
            "status": "generating",
            "progress": 0,
            "started_at": datetime.now().isoformat()
        }
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        
        return {
            "order_id": order_id,
            "module": module,
            "status": "generating",
            "progress": 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模拟进度失败: {str(e)}") 
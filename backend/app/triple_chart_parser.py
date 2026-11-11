#!/usr/bin/env python3
import argparse
import json
import datetime
from typing import Dict, Any, Tuple
import sys
import math

# 导入必要的库
try:
    import sxtwl
    HAS_SXTWL = True
except ImportError:
    HAS_SXTWL = False

try:
    from py_iztro import Astro
    HAS_IZTRO = True
except ImportError:
    HAS_IZTRO = False

try:
    from flatlib import const
    from flatlib.chart import Chart
    from flatlib.datetime import Datetime
    from flatlib.geopos import GeoPos
    HAS_FLATLIB = True
except ImportError:
    HAS_FLATLIB = False

# 导入印度星盘API
try:
    try:
        from .vedic_chart_api import get_vedic_chart  # 相对导入
    except ImportError:
        try:
            from app.vedic_chart_api import get_vedic_chart  # 绝对导入
        except ImportError:
            from vedic_chart_api import get_vedic_chart  # 直接导入
    HAS_VEDIC_API = True
except ImportError:
    HAS_VEDIC_API = False

# 导入高级紫微斗数API
try:
    try:
        from .ziwei_advanced_api import ZiweiAdvancedAPI  # 相对导入
    except ImportError:
        try:
            from app.ziwei_advanced_api import ZiweiAdvancedAPI  # 绝对导入
        except ImportError:
            from ziwei_advanced_api import ZiweiAdvancedAPI  # 直接导入
    HAS_ZIWEI_ADVANCED = True
except ImportError:
    HAS_ZIWEI_ADVANCED = False

# 导入增强八字分析器
try:
    try:
        from .bazi_enhanced_analyzer import BaziEnhancedAnalyzer  # 相对导入
    except ImportError:
        try:
            from app.bazi_enhanced_analyzer import BaziEnhancedAnalyzer  # 绝对导入
        except ImportError:
            from bazi_enhanced_analyzer import BaziEnhancedAnalyzer  # 直接导入
    HAS_BAZI_ENHANCED = True
except ImportError:
    HAS_BAZI_ENHANCED = False

if not any([HAS_SXTWL, HAS_IZTRO, HAS_FLATLIB]):
    print("请至少安装一个依赖库: sxtwl, py-iztro, flatlib", file=sys.stderr)
    print("pip install sxtwl py-iztro flatlib", file=sys.stderr)
    sys.exit(1)

class ZiweiAnalyzer:
    """紫微斗数增强分析器"""
    
    def __init__(self, astrolabe):
        self.astrolabe = astrolabe
        self.palaces = astrolabe.palaces
        
        # 十四主星
        self.major_stars = [
            "紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府",
            "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"
        ]
        
        # 十二宫位
        self.palace_names = [
            "命宫", "父母", "福德", "田宅", "官禄", "仆役", 
            "迁移", "疾厄", "财帛", "子女", "夫妻", "兄弟"
        ]
        
        # 三方四正关系表
        self.tri_relations = {
            "命宫": ["命宫", "财帛", "官禄", "迁移"],
            "父母": ["父母", "疾厄", "田宅", "仆役"],
            "福德": ["福德", "迁移", "财帛", "命宫"],
            "田宅": ["田宅", "子女", "父母", "疾厄"],
            "官禄": ["官禄", "夫妻", "命宫", "财帛"],
            "仆役": ["仆役", "兄弟", "父母", "疾厄"],
            "迁移": ["迁移", "命宫", "福德", "财帛"],
            "疾厄": ["疾厄", "田宅", "父母", "仆役"],
            "财帛": ["财帛", "福德", "官禄", "命宫"],
            "子女": ["子女", "田宅", "夫妻", "兄弟"],
            "夫妻": ["夫妻", "官禄", "子女", "兄弟"],
            "兄弟": ["兄弟", "仆役", "子女", "夫妻"]
        }
    
    # A类：基础信息
    def get_ziwei_chart(self):
        """A1. 返回 12 宫 & 14 主星落宫"""
        chart = {}
        star_positions = {}
        
        for palace in self.palaces:
            palace_info = {
                "index": palace.index,
                "heavenly_stem": palace.heavenly_stem,
                "earthly_branch": palace.earthly_branch,
                "is_body_palace": palace.is_body_palace,
                "major_stars": [],
                "minor_stars": [],
                "adjective_stars": []
            }
            
            # 主星
            for star in palace.major_stars:
                star_info = {
                    "name": star.name,
                    "brightness": getattr(star, 'brightness', ''),
                    "mutagen": getattr(star, 'mutagen', '')
                }
                palace_info["major_stars"].append(star_info)
                star_positions[star.name] = palace.name
            
            # 辅星
            for star in palace.minor_stars:
                palace_info["minor_stars"].append(star.name)
                
            # 煞星
            for star in palace.adjective_stars:
                palace_info["adjective_stars"].append(star.name)
                
            chart[palace.name] = palace_info
            
        return {
            "palaces": chart,
            "star_positions": star_positions
        }
    
    def get_four_pillars(self):
        """A2. 返回四柱干支 (年/月/日/时)"""
        chinese_date = self.astrolabe.chinese_date
        pillars = chinese_date.split(' ')
        
        if len(pillars) >= 4:
            return {
                "year_pillar": pillars[0],
                "month_pillar": pillars[1], 
                "day_pillar": pillars[2],
                "hour_pillar": pillars[3]
            }
        return {"error": "四柱信息解析失败"}
    
    def year_four_trans(self):
        """A3. 年干四化（禄权科忌）"""
        # 从四柱中提取年干
        pillars = self.get_four_pillars()
        if "error" in pillars:
            return {"error": "无法获取年干信息"}
            
        year_pillar = pillars["year_pillar"]
        year_gan = year_pillar[0] if year_pillar else ""
        
        # 年干四化表（简化版）
        four_trans_table = {
            "甲": {"禄": "廉贞", "权": "破军", "科": "武曲", "忌": "太阳"},
            "乙": {"禄": "天机", "权": "天梁", "科": "紫微", "忌": "太阴"},
            "丙": {"禄": "天同", "权": "天机", "科": "文昌", "忌": "廉贞"},
            "丁": {"禄": "太阴", "权": "天同", "科": "天机", "忌": "巨门"},
            "戊": {"禄": "贪狼", "权": "太阴", "科": "右弼", "忌": "天机"},
            "己": {"禄": "武曲", "权": "贪狼", "科": "天梁", "忌": "文曲"},
            "庚": {"禄": "太阳", "权": "武曲", "科": "太阴", "忌": "天同"},
            "辛": {"禄": "巨门", "权": "太阳", "科": "文曲", "忌": "文昌"},
            "壬": {"禄": "天梁", "权": "紫微", "科": "左辅", "忌": "武曲"},
            "癸": {"禄": "破军", "权": "巨门", "科": "太阴", "忌": "贪狼"}
        }
        
        return four_trans_table.get(year_gan, {"error": f"未知年干: {year_gan}"})
    
    def star_position(self, star_name):
        """A4. 给定星耀返回所在宫位"""
        for palace in self.palaces:
            for star in palace.major_stars + palace.minor_stars + palace.adjective_stars:
                if star.name == star_name:
                    return palace.name
        return None
    
    def is_empty_house(self, house_name):
        """A5. 判断宫位是否为空宫"""
        for palace in self.palaces:
            if palace.name == house_name:
                has_major = len(palace.major_stars) > 0
                has_minor = len(palace.minor_stars) > 0
                return not (has_major or has_minor)
        return True
    
    # B类：运势核心
    def major_fortune(self, age):
        """B1. 给定年龄返回大限宫位"""
        # 大限从命宫开始，每10年一个宫位
        start_age = 5  # 一般从5岁开始起大限
        decade = (age - start_age) // 10
        
        # 找到命宫位置
        ming_gong_index = 0
        for i, palace in enumerate(self.palaces):
            if palace.name == "命宫":
                ming_gong_index = i
                break
                
        # 计算大限宫位
        fortune_index = (ming_gong_index + decade) % 12
        return self.palaces[fortune_index].name
    
    def flow_year(self, year):
        """B3. 流年宫位 + 当年主星"""
        # 流年从命宫开始，按地支轮转
        earthly_branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        year_branch_index = (year - 4) % 12  # 甲子年为起点
        
        # 找到对应地支的宫位
        for palace in self.palaces:
            if palace.earthly_branch == earthly_branches[year_branch_index]:
                return {
                    "palace": palace.name,
                    "earthly_branch": palace.earthly_branch,
                    "major_stars": [star.name for star in palace.major_stars]
                }
        
        return {"error": "无法确定流年宫位"}
    
    def flow_trans(self, year):
        """B4. 流年四化"""
        # 根据流年天干确定四化
        heavenly_stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        year_stem = heavenly_stems[(year - 4) % 10]  # 甲子年为起点
        
        return self.year_four_trans_by_stem(year_stem)
    
    def house_of_flow(self, year):
        """B5. 返回流年对应的宫位"""
        flow_result = self.flow_year(year)
        return flow_result.get("palace", "未知")
    
    # C类：三方四正逻辑
    def tri_house(self, house):
        """C1. 返回某宫三方四正宫位数组"""
        return self.tri_relations.get(house, [])
    
    def tri_has_star(self, house, stars):
        """C2. 判断三方四正是否含指定星"""
        tri_houses = self.tri_house(house)
        
        for palace in self.palaces:
            if palace.name in tri_houses:
                palace_stars = [star.name for star in palace.major_stars + palace.minor_stars]
                for star in stars if isinstance(stars, list) else [stars]:
                    if star in palace_stars:
                        return True
        return False
    
    def tri_has_trans(self, house, trans):
        """C3. 判断三方四正是否含四化"""
        tri_houses = self.tri_house(house)
        year_trans = self.year_four_trans()
        
        if "error" in year_trans:
            return False
            
        for palace in self.palaces:
            if palace.name in tri_houses:
                for star in palace.major_stars:
                    if hasattr(star, 'mutagen') and star.mutagen:
                        if trans in ["禄", "权", "科", "忌"] and star.mutagen == trans:
                            return True
        return False
    
    def star_tri_house(self, star):
        """C4. 返回星耀三方四正宫位列表"""
        star_palace = self.star_position(star)
        if star_palace:
            return self.tri_house(star_palace)
        return []
    
    def year_four_trans_by_stem(self, stem):
        """根据天干获取四化"""
        four_trans_table = {
            "甲": {"禄": "廉贞", "权": "破军", "科": "武曲", "忌": "太阳"},
            "乙": {"禄": "天机", "权": "天梁", "科": "紫微", "忌": "太阴"},
            "丙": {"禄": "天同", "权": "天机", "科": "文昌", "忌": "廉贞"},
            "丁": {"禄": "太阴", "权": "天同", "科": "天机", "忌": "巨门"},
            "戊": {"禄": "贪狼", "权": "太阴", "科": "右弼", "忌": "天机"},
            "己": {"禄": "武曲", "权": "贪狼", "科": "天梁", "忌": "文曲"},
            "庚": {"禄": "太阳", "权": "武曲", "科": "太阴", "忌": "天同"},
            "辛": {"禄": "巨门", "权": "太阳", "科": "文曲", "忌": "文昌"},
            "壬": {"禄": "天梁", "权": "紫微", "科": "左辅", "忌": "武曲"},
            "癸": {"禄": "破军", "权": "巨门", "科": "太阴", "忌": "贪狼"}
        }
        
        return four_trans_table.get(stem, {"error": f"未知天干: {stem}"})

class TripleChartParser:
    def __init__(self):
        self.astrolabe = None
        
    def parse_input(self, birth_date: str, birth_time: str, timezone: str, longitude: float, latitude: float, gender: int, daylight_saving: bool = False) -> Dict[str, Any]:
        """解析输入参数"""
        try:
            # 解析日期时间
            date_obj = datetime.datetime.strptime(birth_date, "%Y-%m-%d")
            time_obj = datetime.datetime.strptime(birth_time, "%H:%M").time()
            
            # 解析时区
            tz_sign = 1 if timezone.startswith('+') else -1
            tz_hours = float(timezone[1:])  # 支持 +5.5 这类半小时时区
            tz_offset = tz_sign * tz_hours
            
            # 计算真太阳时
            true_solar_time = self.calculate_true_solar_time(
                date_obj, time_obj, longitude, tz_offset, daylight_saving
            )
            
            return {
                "birth_date": birth_date,
                "birth_time": birth_time,
                "timezone": timezone,
                "longitude": longitude,
                "latitude": latitude,
                "gender": gender,
                "gender_str": "男" if gender == 1 else "女",
                "true_solar_time": true_solar_time,
                "date_obj": date_obj,
                "time_obj": time_obj,
                "tz_offset": tz_offset
            }
        except Exception as e:
            raise ValueError(f"参数解析错误: {e}")
    
    def calculate_true_solar_time(self, date_obj: datetime.date, time_obj: datetime.time, 
                                longitude: float, tz_offset: float, daylight_saving: bool = False) -> datetime.datetime:
        """计算真太阳时"""
        # 经度时差修正（每15度1小时）
        longitude_correction = longitude / 15.0
        
        # 夏令时修正：时区偏移已由 timezone_utils 按出生日期计算（本身含当日 DST），
        # 这里再减 1 小时必然双算——历史 bug：勾选夏令时连珠海（无 DST）都会平移 1 小时。
        # 参数保留兼容旧客户端，恒不生效。
        dst_correction = 0.0
        
        # 结合日期和时间
        dt = datetime.datetime.combine(date_obj, time_obj)
        
        # 计算真太阳时
        # 公式：真太阳时 = 当地时间 + 经度修正 - 时区偏移 + 夏令时修正
        true_dt = dt + datetime.timedelta(hours=longitude_correction - tz_offset + dst_correction)
        
        return true_dt
    
    def calculate_hour_pillar_traditional(self, day_master: str, hour: int) -> str:
        """使用传统口诀计算时柱"""
        # 时干推算口诀：甲己还加甲，乙庚丙作初，丙辛从戊起，丁壬庚子居，戊癸何方发，壬子是真途
        day_gan_rules = {
            "甲": "甲", "己": "甲",  # 甲己还加甲
            "乙": "丙", "庚": "丙",  # 乙庚丙作初
            "丙": "戊", "辛": "戊",  # 丙辛从戊起
            "丁": "庚", "壬": "庚",  # 丁壬庚子居
            "戊": "壬", "癸": "壬"   # 戊癸何方发，壬子是真途
        }
        
        gan_names = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        zhi_names = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        
        # 计算时辰索引
        time_index = (hour + 1) // 2 % 12
        
        # 获取子时开始的天干
        zi_shi_gan = day_gan_rules[day_master]
        zi_gan_index = gan_names.index(zi_shi_gan)
        
        # 计算当前时辰的天干
        shi_gan_index = (zi_gan_index + time_index) % 10
        shi_gan = gan_names[shi_gan_index]
        
        # 当前时辰的地支
        shi_zhi = zhi_names[time_index]
        
        return shi_gan + shi_zhi
    
    def calculate_bazi(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算八字"""
        if not HAS_SXTWL:
            return {"error": "sxtwl库未安装，无法计算八字"}
            
        try:
            true_dt = input_data["true_solar_time"]
            
            # 使用sxtwl计算八字
            day = sxtwl.fromSolar(true_dt.year, true_dt.month, true_dt.day)
            
            # 获取年、月、日干支数据（这些是正确的）
            year_gz = day.getYearGZ()
            month_gz = day.getMonthGZ()
            day_gz = day.getDayGZ()
            
            # 天干地支对照表
            gan_names = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
            zhi_names = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
            
            # 组合年、月、日柱
            year_pillar = gan_names[year_gz.tg] + zhi_names[year_gz.dz]
            month_pillar = gan_names[month_gz.tg] + zhi_names[month_gz.dz]
            day_pillar = gan_names[day_gz.tg] + zhi_names[day_gz.dz]
            day_master = gan_names[day_gz.tg]
            
            # 使用传统口诀计算时柱（修正sxtwl的bug）
            hour_pillar = self.calculate_hour_pillar_traditional(day_master, true_dt.hour)
            
            # 五行统计
            wuxing_map = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", 
                         "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
            zhi_wuxing_map = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火", 
                             "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
            
            five_elements = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
            pillars = [year_pillar, month_pillar, day_pillar, hour_pillar]
            
            for pillar in pillars:
                gan = pillar[0]
                zhi = pillar[1]
                if gan in wuxing_map:
                    five_elements[wuxing_map[gan]] += 1
                if zhi in zhi_wuxing_map:
                    five_elements[zhi_wuxing_map[zhi]] += 1
            
            # 判断身强身弱（简化版）
            day_element = wuxing_map.get(day_master, "未知")
            same_element_count = five_elements.get(day_element, 0)
            total_elements = sum(five_elements.values())
            
            body_strength = "强" if same_element_count / total_elements > 0.3 else "弱"
            
            # 计算十神
            ten_gods = self.calculate_ten_gods(day_master, [year_pillar[0], month_pillar[0], day_pillar[0], hour_pillar[0]])
            
            # 计算纳音
            nayin = self.calculate_nayin(pillars)
            
            # 计算神煞
            spirits = self.calculate_spirits(year_pillar, month_pillar, day_pillar, hour_pillar)
            
            # 计算大运
            dayun = self.calculate_dayun(input_data["gender"], month_pillar, day_gz)
            
            # 基础八字结果
            basic_result = {
                "year_pillar": year_pillar,
                "month_pillar": month_pillar,
                "day_pillar": day_pillar,
                "hour_pillar": hour_pillar,
                "day_master": day_master,
                "five_elements_count": five_elements,
                "body_strength": body_strength,
                "ten_gods": ten_gods,
                "nayin": nayin,
                "spirits": spirits,
                "dayun": dayun,
                "lunar_date": "暂未实现",
                "solar_terms": {
                    "current_term": "未实现",
                    "next_term": "未实现"
                }
            }
            
            # 如果有增强分析器，进行增强分析
            if HAS_BAZI_ENHANCED:
                try:
                    analyzer = BaziEnhancedAnalyzer()
                    enhanced_result = analyzer.enhance_bazi_result(basic_result)
                    return enhanced_result
                except Exception as e:
                    # 如果增强分析失败，返回基础结果并添加错误信息
                    basic_result["enhanced_error"] = f"增强分析失败: {e}"
                    return basic_result
            else:
                return basic_result
        except Exception as e:
            return {"error": f"八字计算错误: {e}"}
    
    def calculate_ten_gods(self, day_master: str, gan_list: list) -> Dict[str, str]:
        """计算十神"""
        ten_gods_map = {
            "甲": {"甲": "比肩", "乙": "劫财", "丙": "食神", "丁": "伤官", "戊": "偏财", "己": "正财", "庚": "七杀", "辛": "正官", "壬": "偏印", "癸": "正印"},
            "乙": {"甲": "劫财", "乙": "比肩", "丙": "伤官", "丁": "食神", "戊": "正财", "己": "偏财", "庚": "正官", "辛": "七杀", "壬": "正印", "癸": "偏印"},
            "丙": {"甲": "偏印", "乙": "正印", "丙": "比肩", "丁": "劫财", "戊": "食神", "己": "伤官", "庚": "偏财", "辛": "正财", "壬": "七杀", "癸": "正官"},
            "丁": {"甲": "正印", "乙": "偏印", "丙": "劫财", "丁": "比肩", "戊": "伤官", "己": "食神", "庚": "正财", "辛": "偏财", "壬": "正官", "癸": "七杀"},
            "戊": {"甲": "七杀", "乙": "正官", "丙": "偏印", "丁": "正印", "戊": "比肩", "己": "劫财", "庚": "食神", "辛": "伤官", "壬": "偏财", "癸": "正财"},
            "己": {"甲": "正官", "乙": "七杀", "丙": "正印", "丁": "偏印", "戊": "劫财", "己": "比肩", "庚": "伤官", "辛": "食神", "壬": "正财", "癸": "偏财"},
            "庚": {"甲": "偏财", "乙": "正财", "丙": "七杀", "丁": "正官", "戊": "偏印", "己": "正印", "庚": "比肩", "辛": "劫财", "壬": "食神", "癸": "伤官"},
            "辛": {"甲": "正财", "乙": "偏财", "丙": "正官", "丁": "七杀", "戊": "正印", "己": "偏印", "庚": "劫财", "辛": "比肩", "壬": "伤官", "癸": "食神"},
            "壬": {"甲": "食神", "乙": "伤官", "丙": "偏财", "丁": "正财", "戊": "七杀", "己": "正官", "庚": "偏印", "辛": "正印", "壬": "比肩", "癸": "劫财"},
            "癸": {"甲": "伤官", "乙": "食神", "丙": "正财", "丁": "偏财", "戊": "正官", "己": "七杀", "庚": "正印", "辛": "偏印", "壬": "劫财", "癸": "比肩"}
        }
        
        result = {}
        positions = ["年干", "月干", "日干", "时干"]
        
        for i, gan in enumerate(gan_list):
            if day_master in ten_gods_map and gan in ten_gods_map[day_master]:
                result[positions[i]] = ten_gods_map[day_master][gan]
            else:
                result[positions[i]] = "未知"
                
        return result
    
    def calculate_nayin(self, pillars: list) -> Dict[str, str]:
        """计算纳音"""
        nayin_table = {
            "甲子": "海中金", "乙丑": "海中金", "丙寅": "炉中火", "丁卯": "炉中火", "戊辰": "大林木", "己巳": "大林木",
            "庚午": "路旁土", "辛未": "路旁土", "壬申": "剑锋金", "癸酉": "剑锋金", "甲戌": "山头火", "乙亥": "山头火",
            "丙子": "涧下水", "丁丑": "涧下水", "戊寅": "城头土", "己卯": "城头土", "庚辰": "白蜡金", "辛巳": "白蜡金",
            "壬午": "杨柳木", "癸未": "杨柳木", "甲申": "泉中水", "乙酉": "泉中水", "丙戌": "屋上土", "丁亥": "屋上土",
            "戊子": "霹雳火", "己丑": "霹雳火", "庚寅": "松柏木", "辛卯": "松柏木", "壬辰": "长流水", "癸巳": "长流水",
            "甲午": "砂中金", "乙未": "砂中金", "丙申": "山下火", "丁酉": "山下火", "戊戌": "平地木", "己亥": "平地木",
            "庚子": "壁上土", "辛丑": "壁上土", "壬寅": "金箔金", "癸卯": "金箔金", "甲辰": "覆灯火", "乙巳": "覆灯火",
            "丙午": "天河水", "丁未": "天河水", "戊申": "大驿土", "己酉": "大驿土", "庚戌": "钗钏金", "辛亥": "钗钏金",
            "壬子": "桑柘木", "癸丑": "桑柘木", "甲寅": "大溪水", "乙卯": "大溪水", "丙辰": "沙中土", "丁巳": "沙中土",
            "戊午": "天上火", "己未": "天上火", "庚申": "石榴木", "辛酉": "石榴木", "壬戌": "大海水", "癸亥": "大海水"
        }
        
        result = {}
        positions = ["年柱", "月柱", "日柱", "时柱"]
        
        for i, pillar in enumerate(pillars):
            result[positions[i]] = nayin_table.get(pillar, "未知")
            
        return result
    
    def calculate_spirits(self, year_pillar: str, month_pillar: str, day_pillar: str, hour_pillar: str) -> list:
        """计算神煞"""
        spirits = []
        day_zhi = day_pillar[1]
        year_zhi = year_pillar[1]
        
        # 贵人
        tianyi_table = {
            "甲": ["丑", "未"], "乙": ["子", "申"], "丙": ["亥", "酉"], "丁": ["亥", "酉"], "戊": ["丑", "未"],
            "己": ["子", "申"], "庚": ["丑", "未"], "辛": ["午", "寅"], "壬": ["卯", "巳"], "癸": ["卯", "巳"]
        }
        
        day_gan = day_pillar[0]
        if day_gan in tianyi_table:
            for zhi in [year_zhi, month_pillar[1], hour_pillar[1]]:
                if zhi in tianyi_table[day_gan]:
                    spirits.append("天乙贵人")
                    break
        
        # 桃花
        peach_blossom = {"子": "酉", "丑": "午", "寅": "卯", "卯": "子", "辰": "酉", "巳": "午",
                        "午": "卯", "未": "子", "申": "酉", "酉": "午", "戌": "卯", "亥": "子"}
        
        if day_zhi in peach_blossom:
            target_zhi = peach_blossom[day_zhi]
            for pillar in [year_pillar, month_pillar, hour_pillar]:
                if pillar[1] == target_zhi:
                    spirits.append("桃花")
                    break
        
        # 驿马
        yima_table = {"申": "寅", "子": "寅", "辰": "寅", "寅": "申", "午": "申", "戌": "申",
                     "巳": "亥", "酉": "亥", "丑": "亥", "亥": "巳", "卯": "巳", "未": "巳"}
        
        if day_zhi in yima_table:
            target_zhi = yima_table[day_zhi]
            for pillar in [year_pillar, month_pillar, hour_pillar]:
                if pillar[1] == target_zhi:
                    spirits.append("驿马")
                    break
        
        # 华盖
        huagai_table = {"寅": "戌", "午": "戌", "戌": "戌", "申": "辰", "子": "辰", "辰": "辰",
                       "巳": "丑", "酉": "丑", "丑": "丑", "亥": "未", "卯": "未", "未": "未"}
        
        if day_zhi in huagai_table:
            target_zhi = huagai_table[day_zhi]
            for pillar in [year_pillar, month_pillar, hour_pillar]:
                if pillar[1] == target_zhi:
                    spirits.append("华盖")
                    break
        
        return spirits if spirits else ["无特殊神煞"]
    
    def calculate_dayun(self, gender: int, month_pillar: str, day_gz) -> Dict[str, Any]:
        """计算大运"""
        # 简化的大运计算
        month_gan = month_pillar[0]
        
        # 阳男阴女顺排，阴男阳女逆排
        gan_yang = month_gan in ["甲", "丙", "戊", "庚", "壬"]
        
        if (gender == 1 and gan_yang) or (gender == 0 and not gan_yang):
            # 顺排
            direction = "顺"
        else:
            # 逆排
            direction = "逆"
        
        # 起运年龄（简化计算）
        qiyun_age = 8  # 简化为8岁起运
        
        return {
            "direction": direction,
            "qiyun_age": qiyun_age,
            "note": "大运详细计算需要更复杂的算法"
        }
    
    def calculate_ziwei(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算紫微斗数 - 使用高级API"""
        if not HAS_IZTRO:
            return {"error": "py-iztro库未安装，无法计算紫微斗数"}
            
        if not HAS_ZIWEI_ADVANCED:
            # 如果高级API不可用，回退到基本功能
            return self._calculate_ziwei_basic(input_data)
            
        try:
            true_dt = input_data["true_solar_time"]
            
            # 根据小时计算时辰索引（0-11）
            time_index = (true_dt.hour + 1) // 2 % 12
            
            # 使用高级紫微斗数API
            api = ZiweiAdvancedAPI(
                birth_date=true_dt.strftime("%Y-%m-%d"),
                birth_time_index=time_index,
                gender=input_data["gender_str"]
            )
            
            # 获取完整的紫微斗数信息
            result = {
                "basic_info": api.get_basic_info(),
                "chart": api.get_ziwei_chart(),
                "four_pillars": api.get_four_pillars(),
                "year_four_trans": api.year_four_trans(),
                
                # A类：基础信息功能
                "A_functions": {
                    "star_position_example": api.star_position("紫微"),
                    "is_empty_house_example": api.is_empty_house("命宫")
                },
                
                # B类：运势核心功能
                "B_functions": {
                    "major_fortune_25": api.major_fortune(25),
                    "flow_year_2024": api.flow_year(2024),
                    "flow_trans_2024": api.flow_trans(2024),
                    "house_of_flow_2024": api.house_of_flow(2024)
                },
                
                # C类：三方四正功能
                "C_functions": {
                    "tri_house_ming": api.tri_house("命宫"),
                    "tri_has_star_example": api.tri_has_star("命宫", ["紫微", "天府"]),
                    "tri_has_trans_example": api.tri_has_trans("命宫", "禄"),
                    "star_tri_house_example": api.star_tri_house("紫微")
                },
                
                "enhanced_features": {
                    "A类基础信息": "5个功能全部实现",
                    "B类运势核心": "4个功能全部实现", 
                    "C类三方四正": "4个功能全部实现",
                    "总计": "13个核心功能完整实现"
                }
            }
            
            return result
            
        except Exception as e:
            return {"error": f"紫微斗数高级API计算错误: {e}"}
    
    def _calculate_ziwei_basic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """基础紫微斗数计算（回退功能）"""
        try:
            true_dt = input_data["true_solar_time"]
            
            # 根据小时计算时辰索引（0-11）
            time_index = (true_dt.hour + 1) // 2 % 12
            
            # 使用py-iztro进行紫微斗数排盘
            astro_instance = Astro()
            self.astrolabe = astro_instance.by_solar(
                solar_date_str=true_dt.strftime("%Y-%m-%d"),
                time_index=time_index,
                gender=input_data["gender_str"],
                fix_leap=True,
                language="zh-CN"
            )
            
            # 使用内置分析器
            ziwei_analyzer = ZiweiAnalyzer(self.astrolabe)
            
            return {
                "basic_info": {
                    "lunar_date": self.astrolabe.lunar_date,
                    "chinese_date": self.astrolabe.chinese_date,
                    "soul": self.astrolabe.soul,
                    "body": self.astrolabe.body,
                    "five_elements_class": self.astrolabe.five_elements_class
                },
                "chart": ziwei_analyzer.get_ziwei_chart(),
                "four_pillars": ziwei_analyzer.get_four_pillars(),
                "year_four_trans": ziwei_analyzer.year_four_trans(),
                "enhanced_features": {
                    "note": "使用基础功能（高级API不可用）"
                }
            }
            
        except Exception as e:
            return {"error": f"紫微斗数基础计算错误: {e}"}
    
    def calculate_vedic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算印度星盘（增强版 - 恒星历模式）"""
        if not HAS_FLATLIB:
            return {"error": "flatlib库未安装，无法计算印度星盘"}
            
        # 优先使用原来的完整API
        if HAS_VEDIC_API:
            try:
                # 使用用户原始输入时间（不再用真太阳时）
                date = input_data["birth_date"]
                time = input_data["birth_time"]
                # tz_offset 可能是小数（半小时时区）或负数，拼成 ±HH:MM
                _off = float(input_data.get('tz_offset', 8))
                _abs = abs(_off)
                tz_str = f"{'+' if _off >= 0 else '-'}{int(_abs):02d}:{int(round((_abs - int(_abs)) * 60)):02d}"
                result = get_vedic_chart(
                    date=date,
                    time=time,
                    tz=tz_str,
                    lat=input_data["latitude"],
                    lon=input_data["longitude"]
                )
                
                result["enhanced_features"] = {
                    "note": "使用原来的完整vedic_chart_api（已改为用户输入时间）",
                    "features": [
                        "Lahiri ayanamsa恒星历系统",
                        "完整的行星和轴点信息",
                        "精确的宫位计算",
                        "支持外行星和特殊点"
                    ]
                }
                
                return result
                
            except Exception as e:
                # 如果原来的API失败，回退到内置实现
                print(f"警告：原来的vedic API失败，回退到内置实现: {e}")
        
        # 回退到内置实现
        try:
            # 使用用户原始输入时间（不再用真太阳时）
            date = input_data["birth_date"]
            time = input_data["birth_time"]
            flatlib_dt = Datetime(
                date.replace("-", "/"),
                time + ":00",
                '+00:00'  # 或用 input_data["tz_offset"] 生成的时区
            )
            
            # 创建地理位置（需要转换为度分格式）
            lat = input_data["latitude"]
            lon = input_data["longitude"]
            
            lat_deg = int(abs(lat))
            lat_min = int((abs(lat) - lat_deg) * 60)
            lat_str = f"{lat_deg}{'n' if lat >= 0 else 's'}{lat_min:02d}"
            
            lon_deg = int(abs(lon))
            lon_min = int((abs(lon) - lon_deg) * 60)
            lon_str = f"{lon_deg}{'e' if lon >= 0 else 'w'}{lon_min:02d}"
            
            geo_pos = GeoPos(lat_str, lon_str)
            
            # 定义需要的行星和关键点常量和名称映射
            planet_map = {
                # 主要行星
                const.SUN: "Sun",
                const.MOON: "Moon", 
                const.MERCURY: "Mercury",
                const.VENUS: "Venus",
                const.MARS: "Mars",
                const.JUPITER: "Jupiter",
                const.SATURN: "Saturn",
                # 月亮交点
                const.NORTH_NODE: "North Node",  # 拉胡
                const.SOUTH_NODE: "South Node",  # 凯图
            }
            
            # 外行星和其他重要点（如果可用）
            try:
                planet_map.update({
                    const.URANUS: "Uranus",
                    const.NEPTUNE: "Neptune", 
                    const.PLUTO: "Pluto"
                })
            except:
                pass
            
            # 重要轴点（如果可用）
            axis_points = {}
            try:
                axis_points.update({
                    const.DESC: "Descendant",        # 下降点
                    const.MC: "Midheaven",          # 天顶
                    const.IC: "Imum Coeli",         # 天底
                    const.PARS_FORTUNA: "Pars Fortuna"  # 福点
                })
            except:
                pass
            
            # 创建星盘
            chart = Chart(flatlib_dt, geo_pos)
            
            # Lahiri Ayanamsa值（根据年份调整，这里使用近似值）
            year = int(date.split('-')[0])
            lahiri_ayanamsa = 23.85 + (year - 1998) * 0.0139  # 每年约增加0.0139度
            
            result = {
                "chart_type": "vedic_sidereal",
                "ayanamsa": {
                    "type": "lahiri",
                    "value": round(lahiri_ayanamsa, 2)
                },
                "ascendant": {},
                "planets": {},
                "axis_points": {}
            }
            
            # 星座名称
            signs = [
                "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
            ]
            
            # 获取上升点信息
            asc = chart.get(const.ASC)
            if asc:
                # 应用恒星历修正
                tropical_lon = asc.lon
                sidereal_lon = (tropical_lon - lahiri_ayanamsa) % 360
                
                # 计算恒星历星座
                sidereal_sign_index = int(sidereal_lon // 30)
                sidereal_sign_degree = sidereal_lon % 30
                
                result["ascendant"] = {
                    "sign": signs[sidereal_sign_index],
                    "house": 1,  # 上升点总是在第1宫
                    "lon": round(sidereal_sign_degree, 2)
                }
            
            # 获取行星信息
            for planet_const, planet_name in planet_map.items():
                try:
                    obj = chart.get(planet_const)
                    if obj:
                        # 应用恒星历修正
                        tropical_lon = obj.lon
                        sidereal_lon = (tropical_lon - lahiri_ayanamsa) % 360
                        
                        # 计算恒星历星座
                        sidereal_sign_index = int(sidereal_lon // 30)
                        sidereal_sign_degree = sidereal_lon % 30
                        
                        # 计算宫位（基于恒星历上升点）
                        asc_sidereal_lon = (asc.lon - lahiri_ayanamsa) % 360
                        house_offset = ((sidereal_lon - asc_sidereal_lon) % 360) // 30
                        house = int(house_offset) + 1
                        
                        result["planets"][planet_name] = {
                            "sign": signs[sidereal_sign_index],
                            "house": house,
                            "lon": round(sidereal_sign_degree, 2)
                        }
                        
                except Exception as e:
                    # 如果某个行星获取失败，跳过但不影响其他行星
                    continue
            
            # 获取轴点信息（下降点、天顶、天底、福点等）
            for axis_const, axis_name in axis_points.items():
                try:
                    obj = chart.get(axis_const)
                    if obj:
                        # 应用恒星历修正
                        tropical_lon = obj.lon
                        sidereal_lon = (tropical_lon - lahiri_ayanamsa) % 360
                        
                        # 计算恒星历星座
                        sidereal_sign_index = int(sidereal_lon // 30)
                        sidereal_sign_degree = sidereal_lon % 30
                        
                        # 计算宫位（基于恒星历上升点）
                        asc_sidereal_lon = (asc.lon - lahiri_ayanamsa) % 360
                        house_offset = ((sidereal_lon - asc_sidereal_lon) % 360) // 30
                        house = int(house_offset) + 1
                        
                        result["axis_points"][axis_name] = {
                            "sign": signs[sidereal_sign_index],
                            "house": house,
                            "lon": round(sidereal_sign_degree, 2)
                        }
                        
                except Exception as e:
                    # 如果某个轴点获取失败，跳过但不影响其他轴点
                    continue
            
            return result
            
        except Exception as e:
            return {"error": f"印度星盘计算错误: {e}"}
    
    def generate_output(self, input_data: Dict[str, Any], bazi_result: Dict[str, Any], 
                       ziwei_result: Dict[str, Any], vedic_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成最终输出"""
        # 格式化真太阳时信息
        true_solar_time = input_data.get("true_solar_time")
        true_solar_time_formatted = None
        if true_solar_time:
            true_solar_time_formatted = {
                "year": true_solar_time.year,
                "month": true_solar_time.month,
                "day": true_solar_time.day,
                "hour": true_solar_time.hour,
                "minute": true_solar_time.minute
            }
        
        return {
            "input": {
                "birth_date": input_data["birth_date"],
                "birth_time": input_data["birth_time"],
                "timezone": input_data["timezone"],
                "longitude": input_data["longitude"],
                "latitude": input_data["latitude"],
                "gender": input_data["gender"],
                "gender_str": input_data["gender_str"],
                "true_solar_time": true_solar_time_formatted
            },
            "bazi": bazi_result,
            "ziwei": ziwei_result,
            "vedic": vedic_result
        }

def main():
    parser = argparse.ArgumentParser(description="三种命理系统排盘工具")
    parser.add_argument("--birth-date", required=True, help="出生日期 (格式: YYYY-MM-DD)")
    parser.add_argument("--birth-time", required=True, help="出生时间 (格式: HH:MM)")
    parser.add_argument("--timezone", required=True, help="时区 (格式: +8 或 -5)")
    parser.add_argument("--longitude", type=float, required=True, help="经度")
    parser.add_argument("--latitude", type=float, required=True, help="纬度")
    parser.add_argument("--gender", type=int, choices=[0, 1], required=True, help="性别 (1=男, 0=女)")
    parser.add_argument("--save-file", action='store_true', help="保存为JSON文件")
    parser.add_argument("--location", default="未知地点", help="出生地点名称")
    
    args = parser.parse_args()
    
    try:
        # 创建解析器实例
        parser_instance = TripleChartParser()
        
        # 解析输入参数
        input_data = parser_instance.parse_input(
            args.birth_date, args.birth_time, args.timezone,
            args.longitude, args.latitude, args.gender
        )
        
        # 计算三种命理系统
        bazi_result = parser_instance.calculate_bazi(input_data)
        ziwei_result = parser_instance.calculate_ziwei(input_data)
        vedic_result = parser_instance.calculate_vedic(input_data)
        
        # 生成最终输出
        final_output = parser_instance.generate_output(
            input_data, bazi_result, ziwei_result, vedic_result
        )
        
        # 如果需要保存文件
        if args.save_file:
            # 生成文件名：性别+测算时间+地点+经纬度.json
            date_str = args.birth_date.replace('-', '')
            time_str = args.birth_time.replace(':', '')
            filename = f"{args.gender}_{date_str}_{time_str}_{args.location}_{args.longitude}_{args.latitude}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(final_output, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 排盘结果已保存到: {filename}")
            print(f"📊 文件大小: {len(json.dumps(final_output, ensure_ascii=False, indent=2))} 字节")
        else:
            # 输出JSON结果
            print(json.dumps(final_output, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"程序执行错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 
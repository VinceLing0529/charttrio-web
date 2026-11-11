#!/usr/bin/env python3
"""
紫微斗数高级API
基于py-iztro库，实现完整的紫微斗数分析功能

用法示例：
python ziwei_advanced_api.py --birth-date 1998-05-29 --birth-time 09:00 --age 25
"""

import argparse
import json
from typing import Dict, Any, List, Union
import sys

try:
    from py_iztro import Astro
    HAS_IZTRO = True
except ImportError:
    HAS_IZTRO = False
    print("请安装py-iztro库: pip install py-iztro", file=sys.stderr)
    sys.exit(1)

class ZiweiAdvancedAPI:
    """紫微斗数高级API"""
    
    def __init__(self, birth_date: str, birth_time_index: int, gender: str = "男"):
        """
        初始化紫微斗数分析器
        
        Args:
            birth_date: 出生日期 (格式: YYYY-MM-DD)
            birth_time_index: 时辰索引 (0-11: 子时到亥时)
            gender: 性别 ("男" 或 "女")
        """
        self.birth_date = birth_date
        self.birth_time_index = birth_time_index
        self.gender = gender
        
        # 初始化星盘
        astro = Astro()
        self.astrolabe = astro.by_solar(
            solar_date_str=birth_date,
            time_index=birth_time_index,
            gender=gender,
            fix_leap=True,
            language="zh-CN"
        )
        
        self.palaces = self.astrolabe.palaces
        
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
        
        # 年干四化表
        self.four_trans_table = {
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
    
    # ==================== 基础信息 ====================
    
    def get_basic_info(self) -> Dict[str, Any]:
        """获取基础信息"""
        return {
            "lunar_date": self.astrolabe.lunar_date,
            "chinese_date": self.astrolabe.chinese_date,
            "soul": self.astrolabe.soul,
            "body": self.astrolabe.body,
            "five_elements_class": self.astrolabe.five_elements_class
        }
    
    # ==================== A类：基础信息 ====================
    
    def get_ziwei_chart(self) -> Dict[str, Any]:
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
    
    def get_four_pillars(self) -> Dict[str, str]:
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
    
    def year_four_trans(self, ganzhi: str = None) -> Dict[str, str]:
        """A3. 年干四化（禄权科忌）"""
        if ganzhi:
            # 如果提供了干支，使用提供的干支
            year_gan = ganzhi[0] if ganzhi else ""
        else:
            # 否则从四柱中提取年干
            pillars = self.get_four_pillars()
            if "error" in pillars:
                return {"error": "无法获取年干信息"}
            year_pillar = pillars["year_pillar"]
            year_gan = year_pillar[0] if year_pillar else ""
        
        return self.four_trans_table.get(year_gan, {"error": f"未知年干: {year_gan}"})
    
    def star_position(self, star_name: str) -> Union[str, None]:
        """A4. 给定星耀返回所在宫位"""
        for palace in self.palaces:
            for star in palace.major_stars + palace.minor_stars + palace.adjective_stars:
                if star.name == star_name:
                    return palace.name
        return None
    
    def is_empty_house(self, house_name: str) -> bool:
        """A5. 判断宫位是否为空宫"""
        for palace in self.palaces:
            if palace.name == house_name:
                has_major = len(palace.major_stars) > 0
                has_minor = len(palace.minor_stars) > 0
                return not (has_major or has_minor)
        return True
    
    # ==================== B类：运势核心 ====================
    
    def major_fortune(self, age: int) -> str:
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
    
    def flow_year(self, year: int) -> Dict[str, Any]:
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
                    "major_stars": [star.name for star in palace.major_stars],
                    "minor_stars": [star.name for star in palace.minor_stars]
                }
        
        return {"error": "无法确定流年宫位"}
    
    def flow_trans(self, year: int) -> Dict[str, str]:
        """B4. 流年四化"""
        # 根据流年天干确定四化
        heavenly_stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        year_stem = heavenly_stems[(year - 4) % 10]  # 甲子年为起点
        
        return self.four_trans_table.get(year_stem, {"error": f"未知年干: {year_stem}"})
    
    def house_of_flow(self, year: int) -> str:
        """B5. 返回流年对应的宫位"""
        flow_result = self.flow_year(year)
        return flow_result.get("palace", "未知")
    
    # ==================== C类：三方四正逻辑 ====================
    
    def tri_house(self, house: str) -> List[str]:
        """C1. 返回某宫三方四正宫位数组"""
        return self.tri_relations.get(house, [])
    
    def tri_has_star(self, house: str, stars: Union[str, List[str]]) -> bool:
        """C2. 判断三方四正是否含指定星"""
        tri_houses = self.tri_house(house)
        stars_list = stars if isinstance(stars, list) else [stars]
        
        for palace in self.palaces:
            if palace.name in tri_houses:
                palace_stars = [star.name for star in palace.major_stars + palace.minor_stars]
                for star in stars_list:
                    if star in palace_stars:
                        return True
        return False
    
    def tri_has_trans(self, house: str, trans: str) -> bool:
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
    
    def star_tri_house(self, star: str) -> List[str]:
        """C4. 返回星耀三方四正宫位列表"""
        star_palace = self.star_position(star)
        if star_palace:
            return self.tri_house(star_palace)
        return []
    
    # ==================== 综合分析 ====================
    
    def comprehensive_analysis(self, age: int = None, target_year: int = None) -> Dict[str, Any]:
        """综合分析报告"""
        result = {
            "basic_info": {
                "birth_date": self.birth_date,
                "gender": self.gender,
                "lunar_date": self.astrolabe.lunar_date,
                "chinese_date": self.astrolabe.chinese_date,
                "soul": self.astrolabe.soul,
                "body": self.astrolabe.body,
                "five_elements_class": self.astrolabe.five_elements_class
            },
            "chart_analysis": self.get_ziwei_chart(),
            "four_pillars": self.get_four_pillars(),
            "year_four_trans": self.year_four_trans(),
            "empty_houses": []
        }
        
        # 空宫分析
        for palace_name in self.palace_names:
            if self.is_empty_house(palace_name):
                result["empty_houses"].append(palace_name)
        
        # 如果提供了年龄，加入大限分析
        if age:
            result["major_fortune"] = {
                "age": age,
                "palace": self.major_fortune(age)
            }
        
        # 如果提供了目标年份，加入流年分析
        if target_year:
            result["flow_analysis"] = {
                "year": target_year,
                "flow_year": self.flow_year(target_year),
                "flow_trans": self.flow_trans(target_year),
                "house_of_flow": self.house_of_flow(target_year)
            }
        
        return result

def main():
    parser = argparse.ArgumentParser(description="紫微斗数高级API")
    parser.add_argument("--birth-date", required=True, help="出生日期 (格式: YYYY-MM-DD)")
    parser.add_argument("--birth-time", type=int, default=4, help="时辰索引 (0-11)")
    parser.add_argument("--gender", default="男", help="性别 (男/女)")
    parser.add_argument("--age", type=int, help="当前年龄")
    parser.add_argument("--target-year", type=int, help="目标分析年份")
    
    # API功能选择
    parser.add_argument("--get-chart", action="store_true", help="获取星盘图")
    parser.add_argument("--get-pillars", action="store_true", help="获取四柱")
    parser.add_argument("--get-trans", action="store_true", help="获取年干四化")
    parser.add_argument("--star-pos", help="查询星耀位置")
    parser.add_argument("--empty-house", help="判断是否空宫")
    parser.add_argument("--tri-house", help="获取三方四正")
    parser.add_argument("--comprehensive", action="store_true", help="综合分析")
    
    args = parser.parse_args()
    
    try:
        # 创建API实例
        api = ZiweiAdvancedAPI(args.birth_date, args.birth_time, args.gender)
        
        result = {}
        
        if args.get_chart:
            result["chart"] = api.get_ziwei_chart()
        
        if args.get_pillars:
            result["four_pillars"] = api.get_four_pillars()
            
        if args.get_trans:
            result["year_four_trans"] = api.year_four_trans()
            
        if args.star_pos:
            result["star_position"] = {
                "star": args.star_pos,
                "palace": api.star_position(args.star_pos)
            }
            
        if args.empty_house:
            result["empty_house"] = {
                "house": args.empty_house,
                "is_empty": api.is_empty_house(args.empty_house)
            }
            
        if args.tri_house:
            result["tri_house"] = {
                "house": args.tri_house,
                "tri_houses": api.tri_house(args.tri_house)
            }
        
        if args.comprehensive:
            result = api.comprehensive_analysis(args.age, args.target_year)
        
        # 如果没有指定功能，默认进行综合分析
        if not any([args.get_chart, args.get_pillars, args.get_trans, args.star_pos, 
                   args.empty_house, args.tri_house, args.comprehensive]):
            result = api.comprehensive_analysis(args.age, args.target_year)
        
        # 输出结果
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"API调用错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 
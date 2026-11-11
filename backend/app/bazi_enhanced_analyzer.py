#!/usr/bin/env python3
"""
增强八字分析器
基于规则表进行详细的八字推理分析
"""

import json
import os
from typing import Dict, List, Any, Optional

class BaziEnhancedAnalyzer:
    """增强八字分析器"""
    
    def __init__(self):
        """初始化分析器，加载规则表"""
        self.rules = self._load_rules()
        
        # 十二长生对应表（长生、沐浴、冠带、临官、帝旺、衰、病、死、墓、绝、胎、养）
        self.twelve_states = [
            "长生", "沐浴", "冠带", "临官", "帝旺", "衰", 
            "病", "死", "墓", "绝", "胎", "养"
        ]
        
    def _load_rules(self) -> Dict[str, Any]:
        """加载规则表"""
        try:
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            rules_file = os.path.join(current_dir, 'bazi_rule_tables.json')
            
            with open(rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"警告：无法加载规则表 {e}")
            return {}
    
    def get_canggan(self, dizhi: str) -> List[str]:
        """获取地支藏干"""
        return self.rules.get("藏干", {}).get(dizhi, [])
    
    def get_nayin(self, ganzhi: str) -> str:
        """获取干支纳音"""
        return self.rules.get("纳音", {}).get(ganzhi, "未知")
    
    def get_kongwang(self, day_ganzhi: str) -> List[str]:
        """获取空亡地支（基于日柱）"""
        return self.rules.get("空亡旬空", {}).get(day_ganzhi, [])
    
    def check_pillar_kongwang(self, dizhi: str, day_ganzhi: str) -> str:
        """检查单个柱子的地支是否空亡"""
        kongwang_list = self.get_kongwang(day_ganzhi)
        return "空亡" if dizhi in kongwang_list else "无"
    
    def get_twelve_state(self, day_gan: str, dizhi: str) -> str:
        """获取十二长生状态"""
        if day_gan not in self.rules.get("长生十二神", {}):
            return "未知"
            
        state_list = self.rules["长生十二神"][day_gan]
        
        try:
            # 找到地支在长生序列中的位置
            state_index = state_list.index(dizhi)
            return self.twelve_states[state_index]
        except (ValueError, IndexError):
            return "未知"
    
    def get_ten_god(self, day_gan: str, target_gan: str) -> str:
        """计算十神"""
        if not self.rules.get("十神规则"):
            return "未知"
            
        rules = self.rules["十神规则"]
        
        # 获取五行和阴阳属性
        day_wuxing = rules["五行"].get(day_gan)
        day_yinyang = rules["阴阳"].get(day_gan)
        target_wuxing = rules["五行"].get(target_gan)
        target_yinyang = rules["阴阳"].get(target_gan)
        
        if not all([day_wuxing, day_yinyang, target_wuxing, target_yinyang]):
            return "未知"
        
        # 判断关系类型
        relation_type = self._get_relation_type(day_wuxing, target_wuxing, rules["生克逻辑"])
        
        # 判断阴阳性质
        same_yinyang = (day_yinyang == target_yinyang)
        
        # 获取十神名称（阴阳异同判断）
        if relation_type == "同我":
            return "比肩" if same_yinyang else "劫财"
        elif relation_type == "生我":
            return "偏印" if same_yinyang else "正印"  # 修正：同阴阳为偏印，异阴阳为正印
        elif relation_type == "我生":
            return "食神" if same_yinyang else "伤官"
        elif relation_type == "我克":
            return "偏财" if same_yinyang else "正财"  # 修正：同阴阳为偏财，异阴阳为正财
        elif relation_type == "克我":
            return "七杀" if same_yinyang else "正官"  # 修正：同阴阳为七杀，异阴阳为正官
        else:
            return "未知"
    
    def _get_relation_type(self, day_wuxing: str, target_wuxing: str, logic: Dict) -> str:
        """判断五行关系类型"""
        # 同我
        if day_wuxing == target_wuxing:
            return "同我"
        
        # 生我：target_wuxing生day_wuxing
        if logic["我生"].get(target_wuxing) == day_wuxing:
            return "生我"
        
        # 我生：day_wuxing生target_wuxing
        if logic["我生"].get(day_wuxing) == target_wuxing:
            return "我生"
        
        # 我克：day_wuxing克target_wuxing
        if logic["我克"].get(day_wuxing) == target_wuxing:
            return "我克"
        
        # 克我：target_wuxing克day_wuxing
        if logic["我克"].get(target_wuxing) == day_wuxing:
            return "克我"
        
        return "未知"
    
    def analyze_pillar(self, pillar_name: str, tiangan: str, dizhi: str, day_gan: str, day_ganzhi: str) -> Dict[str, Any]:
        """分析单个柱"""
        ganzhi = tiangan + dizhi
        
        return {
            "柱序": pillar_name,
            "天干": tiangan,
            "地支": dizhi,
            "干支": ganzhi,
            "主星": self.get_ten_god(day_gan, tiangan),
            "藏干": self.get_canggan(dizhi),
            "纳音": self.get_nayin(ganzhi),
            "空亡": self.check_pillar_kongwang(dizhi, day_ganzhi),
            "星运（十二长生）": self.get_twelve_state(day_gan, dizhi)
        }
    
    def analyze_canggan_ten_gods(self, canggan_list: List[str], day_gan: str) -> List[Dict[str, str]]:
        """分析藏干的十神"""
        result = []
        for canggan in canggan_list:
            result.append({
                "藏干": canggan,
                "十神": self.get_ten_god(day_gan, canggan)
            })
        return result
    
    def calculate_five_elements(self, year_pillar: str, month_pillar: str, day_pillar: str, hour_pillar: str) -> Dict[str, int]:
        """计算五行分布"""
        if not self.rules.get("十神规则", {}).get("五行"):
            return {}
            
        wuxing_map = self.rules["十神规则"]["五行"]
        
        # 地支五行映射
        zhi_wuxing_map = {
            "子": "水", "丑": "土", "寅": "木", "卯": "木", 
            "辰": "土", "巳": "火", "午": "火", "未": "土",
            "申": "金", "酉": "金", "戌": "土", "亥": "水"
        }
        
        # 初始化五行计数
        five_elements = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        
        # 统计四柱八字的五行分布
        pillars = [year_pillar, month_pillar, day_pillar, hour_pillar]
        
        for pillar in pillars:
            if len(pillar) >= 2:
                gan = pillar[0]  # 天干
                zhi = pillar[1]  # 地支
                
                # 天干五行
                if gan in wuxing_map:
                    five_elements[wuxing_map[gan]] += 1
                
                # 地支五行
                if zhi in zhi_wuxing_map:
                    five_elements[zhi_wuxing_map[zhi]] += 1
        
        return five_elements
    
    def enhance_bazi_result(self, bazi_result: Dict[str, Any]) -> Dict[str, Any]:
        """增强八字结果"""
        if "error" in bazi_result:
            return bazi_result
        
        try:
            # 提取基础信息
            year_pillar = bazi_result.get("year_pillar", "")
            month_pillar = bazi_result.get("month_pillar", "")
            day_pillar = bazi_result.get("day_pillar", "")
            hour_pillar = bazi_result.get("hour_pillar", "")
            day_master = bazi_result.get("day_master", "")
            
            if not all([year_pillar, month_pillar, day_pillar, hour_pillar, day_master]):
                return {"error": "八字信息不完整"}
            
            # 分析四柱
            pillars_analysis = []
            
            # 年柱
            if len(year_pillar) >= 2:
                pillars_analysis.append(self.analyze_pillar(
                    "年柱", year_pillar[0], year_pillar[1], day_master, day_pillar
                ))
            
            # 月柱
            if len(month_pillar) >= 2:
                pillars_analysis.append(self.analyze_pillar(
                    "月柱", month_pillar[0], month_pillar[1], day_master, day_pillar
                ))
            
            # 日柱
            if len(day_pillar) >= 2:
                pillars_analysis.append(self.analyze_pillar(
                    "日柱", day_pillar[0], day_pillar[1], day_master, day_pillar
                ))
            
            # 时柱
            if len(hour_pillar) >= 2:
                pillars_analysis.append(self.analyze_pillar(
                    "时柱", hour_pillar[0], hour_pillar[1], day_master, day_pillar
                ))
            
            # 分析藏干十神
            for pillar in pillars_analysis:
                pillar["藏干十神"] = self.analyze_canggan_ten_gods(
                    pillar["藏干"], day_master
                )
            
            # 计算五行分布
            five_elements_distribution = self.calculate_five_elements(
                year_pillar, month_pillar, day_pillar, hour_pillar
            )
            
            # 统计十神分布
            ten_gods_count = {}
            for pillar in pillars_analysis:
                # 天干十神
                main_god = pillar["主星"]
                ten_gods_count[main_god] = ten_gods_count.get(main_god, 0) + 1
                
                # 藏干十神
                for canggan_info in pillar["藏干十神"]:
                    canggan_god = canggan_info["十神"]
                    ten_gods_count[canggan_god] = ten_gods_count.get(canggan_god, 0) + 1
            
            # 增强的八字结果
            enhanced_result = {
                **bazi_result,  # 保留原有信息
                "five_elements": five_elements_distribution,  # 添加五行分布
                "enhanced_analysis": {
                    "四柱详析": pillars_analysis,
                    "十神统计": ten_gods_count,
                    "五行分布": five_elements_distribution,
                    "分析说明": {
                        "主星": "天干对应的十神",
                        "藏干": "地支中隐藏的天干",
                        "纳音": "干支组合的五行属性",
                        "空亡": "基于日柱的空亡地支",
                        "星运": "基于日干的十二长生状态",
                        "五行": "四柱八字中五行元素的分布统计"
                    }
                }
            }
            
            return enhanced_result
            
        except Exception as e:
            return {"error": f"增强分析失败: {e}"}

def test_enhanced_analyzer():
    """测试增强分析器"""
    analyzer = BaziEnhancedAnalyzer()
    
    # 测试数据（庚辰 甲申 丙午 癸巳）
    test_bazi = {
        "year_pillar": "庚辰",
        "month_pillar": "甲申", 
        "day_pillar": "丙午",
        "hour_pillar": "癸巳",
        "day_master": "丙",
        "body_strength": "强"
    }
    
    result = analyzer.enhance_bazi_result(test_bazi)
    
    print("=== 增强八字分析测试 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    test_enhanced_analyzer() 
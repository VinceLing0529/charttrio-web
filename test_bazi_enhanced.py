import sys
import os
sys.path.append('backend')

from app.triple_chart_parser import TripleChartParser
from app.core.timezone_utils import get_timezone_from_coordinates, format_timezone_offset
import json

def test_bazi_enhanced():
    print("=== 测试八字增强分析 ===")
    
    try:
        # 测试数据
        birth_date = "1995-06-15"
        birth_time = "14:30"
        longitude = 121.5
        latitude = 31.2
        gender = 1
        
        # 获取时区信息
        timezone_info = get_timezone_from_coordinates(longitude, latitude)
        timezone_offset = format_timezone_offset(timezone_info["utc_offset"])
        
        print(f"时区信息: {timezone_offset}")
        
        # 创建解析器
        parser = TripleChartParser()
        
        # 解析输入参数
        input_data = parser.parse_input(
            birth_date=birth_date,
            birth_time=birth_time,
            timezone=timezone_offset,
            longitude=longitude,
            latitude=latitude,
            gender=gender
        )
        
        print(f"✓ 输入数据解析成功")
        
        # 计算八字
        bazi_result = parser.calculate_bazi(input_data)
        
        print(f"✓ 八字计算完成")
        print(f"八字结果键: {list(bazi_result.keys())}")
        
        # 检查是否有增强分析
        if 'enhanced_analysis' in bazi_result:
            enhanced = bazi_result['enhanced_analysis']
            print(f"✓ 找到增强分析数据")
            print(f"增强分析键: {list(enhanced.keys())}")
            
            # 显示四柱详析
            if '四柱详析' in enhanced:
                pillars = enhanced['四柱详析']
                print("\n=== 四柱详析 ===")
                print(f"四柱详析数据类型: {type(pillars)}")
                if isinstance(pillars, list):
                    for i, pillar_data in enumerate(pillars):
                        print(f"\n第{i+1}柱:")
                        if isinstance(pillar_data, dict):
                            for key, value in pillar_data.items():
                                print(f"  {key}: {value}")
                        else:
                            print(f"  {pillar_data}")
                elif isinstance(pillars, dict):
                    for pillar_name, pillar_data in pillars.items():
                        print(f"\n{pillar_name}:")
                        if isinstance(pillar_data, dict):
                            for key, value in pillar_data.items():
                                print(f"  {key}: {value}")
                        else:
                            print(f"  {pillar_data}")
                else:
                    print(f"未知的四柱详析数据格式: {pillars}")
            
            # 显示十神统计
            if '十神统计' in enhanced:
                print(f"\n=== 十神统计 ===")
                stats = enhanced['十神统计']
                for god, count in stats.items():
                    print(f"{god}: {count}")
            
            # 显示分析说明
            if '分析说明' in enhanced:
                print(f"\n=== 分析说明 ===")
                print(enhanced['分析说明'])
                    
        else:
            print('❌ 没有找到增强分析数据!')
                
        # 生成完整输出看看前端会收到什么数据
        ziwei_result = parser.calculate_ziwei(input_data)
        vedic_result = parser.calculate_vedic(input_data)
        output = parser.generate_output(input_data, bazi_result, ziwei_result, vedic_result)
        
        print(f"\n=== 前端会收到的数据结构 ===")
        if 'charts' in output:
            charts = output['charts']
            print(f"图表键: {list(charts.keys())}")
            if 'bazi' in charts:
                bazi_output = charts['bazi']
                print(f"八字输出键: {list(bazi_output.keys())}")
                
                # 检查前端数据中的增强分析
                if 'enhanced_analysis' in bazi_output:
                    enhanced_output = bazi_output['enhanced_analysis']
                    print(f"前端增强分析键: {list(enhanced_output.keys())}")
                    
                    # 检查四柱详析是否正确传递
                    if '四柱详析' in enhanced_output:
                        print("✓ 四柱详析数据已传递到前端")
                        # 显示一个柱的详细信息作为示例
                        pillars_output = enhanced_output['四柱详析']
                        if '年柱' in pillars_output:
                            print(f"年柱示例: {pillars_output['年柱']}")
                    else:
                        print("❌ 四柱详析数据未传递到前端")
                else:
                    print("❌ 前端数据中没有增强分析")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bazi_enhanced() 
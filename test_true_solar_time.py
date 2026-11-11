#!/usr/bin/env python3
"""
测试真太阳时计算的准确性
"""

import requests
import json
from datetime import datetime

def test_true_solar_time():
    """测试真太阳时计算"""
    base_url = "http://127.0.0.1:8000"
    
    # 测试案例：不同地点和夏令时情况
    test_cases = [
        {
            "name": "北京（无夏令时）",
            "birth_date": "2023-06-21",  # 夏至日
            "birth_time": "12:00",       # 正午
            "longitude": 116.4,
            "latitude": 39.9,
            "daylight_saving": False,
            "expected_description": "北京时间12:00，经度116.4°，应该接近真太阳时12:00"
        },
        {
            "name": "北京（模拟夏令时）",
            "birth_date": "2023-06-21",
            "birth_time": "12:00",
            "longitude": 116.4,
            "latitude": 39.9,
            "daylight_saving": True,
            "expected_description": "北京时间12:00+夏令时，真太阳时应该提前1小时"
        },
        {
            "name": "上海（无夏令时）",
            "birth_date": "2023-06-21",
            "birth_time": "12:00",
            "longitude": 121.5,
            "latitude": 31.2,
            "daylight_saving": False,
            "expected_description": "上海经度121.5°，比北京偏东，真太阳时应该稍晚"
        },
        {
            "name": "乌鲁木齐（无夏令时）",
            "birth_date": "2023-06-21",
            "birth_time": "12:00",
            "longitude": 87.6,
            "latitude": 43.8,
            "daylight_saving": False,
            "expected_description": "乌鲁木齐经度87.6°，比北京偏西，真太阳时应该明显提前"
        },
        {
            "name": "纽约（夏令时）",
            "birth_date": "2023-06-21",
            "birth_time": "12:00",
            "longitude": -74.0,
            "latitude": 40.7,
            "daylight_saving": True,
            "expected_description": "纽约夏令时12:00，西经74°，真太阳时计算"
        },
        {
            "name": "伦敦（夏令时）",
            "birth_date": "2023-06-21",
            "birth_time": "12:00",
            "longitude": -0.1,
            "latitude": 51.5,
            "daylight_saving": True,
            "expected_description": "伦敦夏令时12:00，接近本初子午线，真太阳时计算"
        }
    ]
    
    print("=" * 100)
    print("真太阳时计算测试")
    print("=" * 100)
    
    for test_case in test_cases:
        try:
            # 调用API
            response = requests.post(
                f"{base_url}/api/charts/bazi-only",
                json={
                    "birth_date": test_case["birth_date"],
                    "birth_time": test_case["birth_time"],
                    "longitude": test_case["longitude"],
                    "latitude": test_case["latitude"],
                    "gender": 1,
                    "location_name": test_case["name"],
                    "daylight_saving": test_case["daylight_saving"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    result_data = data["data"]
                    input_data = result_data["input"]
                    bazi_data = result_data["bazi"]
                    
                    # 提取真太阳时信息（处理ISO格式字符串）
                    true_solar_time_str = input_data.get("true_solar_time")
                    if true_solar_time_str:
                        # 解析ISO格式时间字符串
                        true_solar_time = datetime.fromisoformat(true_solar_time_str.replace('T', ' '))
                        true_time_str = true_solar_time.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # 计算时差
                        input_datetime = datetime.strptime(f"{test_case['birth_date']} {test_case['birth_time']}", "%Y-%m-%d %H:%M")
                        time_diff = (true_solar_time - input_datetime).total_seconds() / 3600
                        time_diff_str = f"{time_diff:+.2f}小时"
                    else:
                        true_time_str = "未获取到"
                        time_diff_str = "计算失败"
                    
                    print(f"📍 {test_case['name']}")
                    print(f"   输入时间: {test_case['birth_date']} {test_case['birth_time']}")
                    print(f"   经纬度: {test_case['longitude']}, {test_case['latitude']}")
                    print(f"   夏令时: {'是' if test_case['daylight_saving'] else '否'}")
                    print(f"   真太阳时: {true_time_str}")
                    print(f"   时间差: {time_diff_str}")
                    print(f"   八字: {bazi_data.get('year_pillar', '?')}{bazi_data.get('month_pillar', '?')}{bazi_data.get('day_pillar', '?')}{bazi_data.get('hour_pillar', '?')}")
                    print(f"   说明: {test_case['expected_description']}")
                    print()
                else:
                    print(f"❌ {test_case['name']} - API返回错误: {data}")
                    print()
            else:
                print(f"❌ {test_case['name']} - HTTP错误: {response.status_code}")
                print()
                
        except Exception as e:
            print(f"❌ {test_case['name']} - 测试出错: {str(e)}")
            print()
    
    print("=" * 100)
    print("真太阳时计算说明:")
    print("• 真太阳时 = 当地时间 + 经度修正 - 时区偏移 + 夏令时修正")
    print("• 经度修正: 每15度经度对应1小时时差")
    print("• 夏令时修正: 如果使用夏令时，需要减去1小时")
    print("• 中国统一使用北京时间(UTC+8)，但地理位置不同会有真太阳时差异")
    print("=" * 100)

if __name__ == "__main__":
    test_true_solar_time() 
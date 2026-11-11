#!/usr/bin/env python3

import requests
import json

def simple_test():
    """简单的API测试"""
    base_url = "http://127.0.0.1:8000"
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/health")
        print(f"健康检查: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {response.json()}")
    except Exception as e:
        print(f"健康检查失败: {e}")
    
    # 测试简单的八字计算
    try:
        test_data = {
            "birth_date": "2000-01-01",
            "birth_time": "12:00",
            "longitude": 116.4,
            "latitude": 39.9,
            "gender": 1,
            "location_name": "北京",
            "daylight_saving": False
        }
        
        response = requests.post(f"{base_url}/api/charts/bazi-only", json=test_data)
        print(f"\n八字计算: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data.get('success')}")
            print(f"消息: {data.get('message')}")
            
            if data.get('success') and 'data' in data:
                result_data = data['data']
                input_info = result_data.get('input', {})
                bazi_info = result_data.get('bazi', {})
                
                print(f"真太阳时: {input_info.get('true_solar_time')}")
                print(f"八字: {bazi_info.get('year_pillar')}{bazi_info.get('month_pillar')}{bazi_info.get('day_pillar')}{bazi_info.get('hour_pillar')}")
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"八字计算失败: {e}")

if __name__ == "__main__":
    simple_test() 
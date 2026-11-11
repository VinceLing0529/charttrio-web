#!/usr/bin/env python3
import requests
import json

def test_api():
    # 测试数据
    data = {
        'birth_date': '2000-01-01',
        'birth_time': '00:00',
        'longitude': 116.4,
        'latitude': 39.9,
        'gender': 1,
        'location_name': '北京'
    }
    
    try:
        # 测试API连接
        print("正在测试API连接...")
        
        # 测试健康检查
        health_response = requests.get('http://localhost:8000/health')
        print(f"健康检查状态: {health_response.status_code}")
        print(f"健康检查响应: {health_response.text}")
        
        # 测试排盘API
        print("\n正在测试排盘API...")
        response = requests.post('http://localhost:8000/api/charts/calculate', json=data)
        print(f"API状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("API调用成功!")
            print(f"响应长度: {len(response.text)}")
            
            # 打印完整的数据结构
            print("\n=== 完整数据结构 ===")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            if 'data' in result:
                print("\n=== 数据字段分析 ===")
                data_keys = result['data'].keys()
                print(f"主要字段: {list(data_keys)}")
                
                if 'bazi' in result['data']:
                    print("\n--- 八字数据结构 ---")
                    bazi_keys = result['data']['bazi'].keys()
                    print(f"八字字段: {list(bazi_keys)}")
                    
                if 'ziwei' in result['data']:
                    print("\n--- 紫微数据结构 ---")
                    ziwei_keys = result['data']['ziwei'].keys()
                    print(f"紫微字段: {list(ziwei_keys)}")
                    
                if 'vedic' in result['data']:
                    print("\n--- 印度星盘数据结构 ---")
                    vedic_keys = result['data']['vedic'].keys()
                    print(f"印度星盘字段: {list(vedic_keys)}")
        else:
            print(f"API调用失败: {response.text}")
            
    except Exception as e:
        print(f"测试出错: {str(e)}")

def test_generate_module():
    url = "http://localhost:8000/api/ai-report/generate-module"
    data = {
        "order_id": "AI202506262345568619ih8lp",
        "module": "analysis"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    test_api()
    test_generate_module() 
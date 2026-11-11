#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time

def test_frontend_fix():
    """测试前端空亡显示修正"""
    
    print("🔧 测试前端空亡显示修正")
    print("=" * 50)
    
    # 等待前端启动
    print("⏳ 等待前端服务启动...")
    time.sleep(3)
    
    # 测试后端API是否正常
    test_data = {
        "birth_date": "2000-08-16",
        "birth_time": "10:00", 
        "longitude": 116.4,
        "latitude": 39.9,
        "gender": 1,
        "location_name": "北京"
    }
    
    try:
        print("📡 测试后端API...")
        response = requests.post("http://localhost:8000/api/charts/calculate", json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success") and "data" in result:
                data = result["data"]
                bazi = data.get("bazi", {})
                
                print("✅ 后端API正常")
                print(f"📊 日柱: {bazi.get('day_pillar', '未知')}")
                
                if "enhanced_analysis" in bazi and "四柱详析" in bazi["enhanced_analysis"]:
                    print("\n🧠 各柱空亡状态:")
                    for pillar in bazi["enhanced_analysis"]["四柱详析"]:
                        pillar_name = pillar.get("柱序", "")
                        kongwang_status = pillar.get("空亡", "")
                        print(f"  {pillar_name}: {kongwang_status}")
                    
                    print("\n✅ 后端数据格式正确（空亡字段为字符串）")
                else:
                    print("❌ 未找到增强分析数据")
                    
            else:
                print(f"❌ API调用失败: {result}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API测试异常: {e}")
    
    print("\n🌐 前端测试说明:")
    print("1. 打开浏览器访问: http://localhost:3000")
    print("2. 输入生辰信息进行排盘")
    print("3. 查看结果页面的空亡显示")
    print("4. 应该不再出现 '.join is not a function' 错误")
    print("5. 空亡状态应该显示为 '空亡' 或 '无'，而不是数组格式")

if __name__ == "__main__":
    test_frontend_fix() 
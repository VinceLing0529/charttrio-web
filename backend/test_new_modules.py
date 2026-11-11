#!/usr/bin/env python3
import requests
import json

def test_new_modules():
    """测试新的四模块设计"""
    
    # 模拟用户数据
    test_user_data = {
        "input": {
            "year": 1995,
            "month": 6,
            "day": 15,
            "hour": 14,
            "minute": 30,
            "location": "上海",
            "gender": "男",
            "longitude": 121.5,
            "latitude": 31.2
        },
        "bazi": {
            "year_pillar": "乙亥",
            "month_pillar": "壬午",
            "day_pillar": "丁巳", 
            "hour_pillar": "辛亥",
            "day_master": "丁火"
        },
        "ziwei": {
            "main_stars": ["紫微", "天府"],
            "palace_info": "命宫在寅宫"
        },
        "vedic": {
            "sun_sign": "Gemini",
            "moon_sign": "Scorpio", 
            "ascendant": "Virgo"
        }
    }
    
    print("🚀 开始测试新的四模块设计...")
    
    try:
        # 1. 设置上下文
        print("\n1️⃣ 设置分析上下文...")
        setup_response = requests.post(
            'http://localhost:8000/ai/analysis/setup-context',
            json={
                "user_data": test_user_data,
                "order_id": "TEST_NEW_MODULES"
            }
        )
        
        if setup_response.status_code == 200:
            print("✅ 上下文设置成功")
        else:
            print(f"❌ 上下文设置失败: {setup_response.text}")
            return
        
        # 2. 批量生成四模块分析
        print("\n2️⃣ 生成四模块分析...")
        analysis_response = requests.post(
            'http://localhost:8000/ai/analysis/batch-generate',
            json={"order_id": "TEST_NEW_MODULES"}
        )
        
        if analysis_response.status_code == 200:
            result = analysis_response.json()
            print("✅ 四模块分析生成成功!")
            
            # 显示结果概要
            print("\n📊 分析结果概要:")
            for module_id, module_data in result['data'].items():
                if module_id != 'final_summary':
                    print(f"  • {module_id}: {'✅ 完成' if module_data else '❌ 空数据'}")
            
            # 保存结果到文件
            with open('test_new_modules_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("\n💾 完整结果已保存到 test_new_modules_result.json")
            
        else:
            print(f"❌ 分析生成失败: {analysis_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保后端服务正在运行")
        print("启动命令: python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_new_modules() 
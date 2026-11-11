#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek API 测试脚本
测试DeepSeek API的基本功能和命理分析能力
"""

import os
import sys
import json
import requests
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")  # 需要设置环境变量
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

def call_deepseek_api(prompt_text, max_retries=3, model="deepseek-chat", temperature=0.7):
    """调用DeepSeek API"""
    if not DEEPSEEK_API_KEY:
        raise Exception("DeepSeek API Key未配置，请设置DEEPSEEK_API_KEY环境变量")
    
    for attempt in range(max_retries):
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
            }
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一位专业的命理分析师，精通八字、紫微斗数、印度星盘等多种命理体系。请根据用户提供的命理信息，给出专业、详细、准确的分析。"},
                    {"role": "user", "content": prompt_text}
                ],
                "temperature": temperature,
                "stream": False
            }
            
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    return content
                else:
                    raise Exception("API返回格式错误")
            else:
                error_detail = ""
                try:
                    error_json = response.json()
                    error_detail = f" - 详细错误: {error_json}"
                except:
                    error_detail = f" - 响应内容: {response.text}"
                raise Exception(f"API请求失败: {response.status_code}{error_detail}")
                
        except requests.exceptions.Timeout:
            print(f"DeepSeek API调用超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                raise Exception("API调用多次超时，请检查网络连接或稍后重试")
            continue
        except Exception as e:
            print(f"DeepSeek API调用错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                raise e
            continue

def test_basic_chat():
    """测试基本对话功能"""
    print("=" * 50)
    print("测试1: 基本对话功能")
    print("=" * 50)
    
    try:
        prompt = "你好，请介绍一下你自己。"
        response = call_deepseek_api(prompt)
        print(f"提问: {prompt}")
        print(f"回答: {response}")
        print("✅ 基本对话测试通过")
    except Exception as e:
        print(f"❌ 基本对话测试失败: {str(e)}")
    
    print("\n")

def test_fortune_analysis():
    """测试命理分析功能"""
    print("=" * 50)
    print("测试2: 命理分析功能")
    print("=" * 50)
    
    try:
        prompt = """
请分析以下八字信息：
出生时间：1995年6月15日14:30
出生地点：上海
八字四柱：乙亥年 壬午月 庚申日 癸未时
日主：庚金
身强身弱：身弱

请从以下几个方面进行分析：
1. 性格特点
2. 事业发展方向
3. 财运分析
4. 感情婚姻
5. 健康注意事项

要求：分析要专业、详细，给出具体的建议。
"""
        response = call_deepseek_api(prompt)
        print(f"提问: {prompt}")
        print(f"回答: {response}")
        print("✅ 命理分析测试通过")
    except Exception as e:
        print(f"❌ 命理分析测试失败: {str(e)}")
    
    print("\n")

def test_json_output():
    """测试JSON格式输出"""
    print("=" * 50)
    print("测试3: JSON格式输出")
    print("=" * 50)
    
    try:
        prompt = """
请分析八字"乙亥年 壬午月 庚申日 癸未时"，并以JSON格式返回分析结果。

要求的JSON格式如下：
{
  "性格特点": {
    "优点": ["优点1", "优点2", "优点3"],
    "缺点": ["缺点1", "缺点2", "缺点3"]
  },
  "事业发展": {
    "适合行业": ["行业1", "行业2", "行业3"],
    "发展建议": "具体建议"
  },
  "财运分析": {
    "财运等级": "强/中/弱",
    "理财建议": "具体建议"
  }
}

请严格按照这个JSON格式返回，不要添加其他文字说明。
"""
        response = call_deepseek_api(prompt)
        print(f"提问: {prompt}")
        print(f"回答: {response}")
        
        # 尝试解析JSON
        try:
            json_data = json.loads(response)
            print("✅ JSON解析成功")
            print(f"解析后的数据: {json.dumps(json_data, ensure_ascii=False, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {str(e)}")
            
        print("✅ JSON格式输出测试通过")
    except Exception as e:
        print(f"❌ JSON格式输出测试失败: {str(e)}")
    
    print("\n")

def test_different_models():
    """测试不同模型"""
    print("=" * 50)
    print("测试4: 不同模型对比")
    print("=" * 50)
    
    models = ["deepseek-chat", "deepseek-reasoner"]
    prompt = "请用一句话解释什么是八字命理。"
    
    for model in models:
        try:
            print(f"测试模型: {model}")
            response = call_deepseek_api(prompt, model=model)
            print(f"回答: {response}")
            print("✅ 模型测试通过")
        except Exception as e:
            print(f"❌ 模型 {model} 测试失败: {str(e)}")
        print("-" * 30)
    
    print("\n")

def main():
    """主函数"""
    print("🚀 开始测试DeepSeek API")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查API Key
    if not DEEPSEEK_API_KEY:
        print("❌ 错误: 请先设置DEEPSEEK_API_KEY环境变量")
        print("设置方法:")
        print("Windows: set DEEPSEEK_API_KEY=your_api_key")
        print("Linux/Mac: export DEEPSEEK_API_KEY=your_api_key")
        return
    
    print(f"✅ API Key已配置 (长度: {len(DEEPSEEK_API_KEY)})")
    print("\n")
    
    # 运行测试
    test_basic_chat()
    test_fortune_analysis()
    test_json_output()
    test_different_models()
    
    print("🎉 所有测试完成!")

if __name__ == "__main__":
    main() 
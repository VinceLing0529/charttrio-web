#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek API 使用示例
展示如何在lifeinsight-web项目中使用DeepSeek API替代Gemini API
"""

import os
import json
import requests
from app.api.ai_report import call_deepseek_api

def example_simple_chat():
    """简单对话示例"""
    print("=== 简单对话示例 ===")
    
    try:
        response = call_deepseek_api("你好，请介绍一下DeepSeek模型的特点。")
        print(f"回答: {response}")
    except Exception as e:
        print(f"错误: {str(e)}")

def example_fortune_telling():
    """命理分析示例"""
    print("\n=== 命理分析示例 ===")
    
    prompt = """
请分析以下八字信息：
八字四柱：乙亥年 壬午月 庚申日 癸未时
日主：庚金
身强身弱：身弱

请简要分析此人的性格特点和事业发展方向。
"""
    
    try:
        response = call_deepseek_api(prompt)
        print(f"分析结果: {response}")
    except Exception as e:
        print(f"错误: {str(e)}")

def example_json_format():
    """JSON格式输出示例"""
    print("\n=== JSON格式输出示例 ===")
    
    prompt = """
请分析八字"乙亥年 壬午月 庚申日 癸未时"，并以JSON格式返回结果：
{
  "性格特点": "性格描述",
  "事业方向": "事业建议",
  "财运": "财运分析"
}

请严格按照JSON格式返回，不要添加其他说明文字。
"""
    
    try:
        response = call_deepseek_api(prompt)
        print(f"原始回答: {response}")
        
        # 尝试解析JSON
        try:
            json_data = json.loads(response)
            print(f"解析成功: {json.dumps(json_data, ensure_ascii=False, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {str(e)}")
            
    except Exception as e:
        print(f"错误: {str(e)}")

def example_different_models():
    """不同模型对比示例"""
    print("\n=== 不同模型对比示例 ===")
    
    prompt = "请用一句话解释什么是八字命理。"
    models = ["deepseek-chat", "deepseek-reasoner"]
    
    for model in models:
        print(f"\n使用模型: {model}")
        try:
            response = call_deepseek_api(prompt, model=model)
            print(f"回答: {response}")
        except Exception as e:
            print(f"错误: {str(e)}")

def example_temperature_comparison():
    """不同temperature参数对比"""
    print("\n=== 不同温度参数对比示例 ===")
    
    prompt = "请为八字命理网站写一个吸引人的标语。"
    temperatures = [0.1, 0.7, 1.0]
    
    for temp in temperatures:
        print(f"\n温度参数: {temp}")
        try:
            response = call_deepseek_api(prompt, temperature=temp)
            print(f"回答: {response}")
        except Exception as e:
            print(f"错误: {str(e)}")

def main():
    """主函数"""
    print("🚀 DeepSeek API 使用示例")
    print("=" * 50)
    
    # 检查API Key
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("❌ 请先设置DEEPSEEK_API_KEY环境变量")
        print("设置方法:")
        print("Windows PowerShell: $env:DEEPSEEK_API_KEY='your_api_key'")
        print("Windows CMD: set DEEPSEEK_API_KEY=your_api_key")
        print("Linux/Mac: export DEEPSEEK_API_KEY=your_api_key")
        print("\n获取API Key: https://platform.deepseek.com/api_keys")
        return
    
    print(f"✅ API Key已配置")
    
    # 运行示例
    example_simple_chat()
    example_fortune_telling()
    example_json_format()
    example_different_models()
    example_temperature_comparison()
    
    print("\n🎉 所有示例运行完成!")
    print("\n💡 提示:")
    print("- 你可以在ai_report.py中将call_gemini_api替换为call_deepseek_api")
    print("- DeepSeek API与OpenAI API格式兼容，易于集成")
    print("- 支持多种模型：deepseek-chat, deepseek-reasoner")
    print("- 价格比较优惠，适合大规模应用")

if __name__ == "__main__":
    main() 
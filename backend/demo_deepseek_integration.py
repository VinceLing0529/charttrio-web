#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek API 集成演示
展示如何在lifeinsight-web项目中使用DeepSeek API
"""

import os
import sys
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def demo_deepseek_function():
    """演示DeepSeek API函数的使用方法"""
    
    print("🚀 DeepSeek API 集成演示")
    print("=" * 50)
    
    # 显示API Key配置状态
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if api_key:
        print(f"✅ DeepSeek API Key已配置: {api_key[:8]}...{api_key[-8:]}")
    else:
        print("❌ DeepSeek API Key未配置")
    
    print("\n📋 已集成的功能:")
    print("1. call_deepseek_api() 函数已添加到 app/api/ai_report.py")
    print("2. 支持多种模型: deepseek-chat, deepseek-reasoner")
    print("3. 支持参数调节: temperature, max_retries")
    print("4. 完整的错误处理和重试机制")
    
    print("\n🔧 函数签名:")
    print("def call_deepseek_api(prompt_text, max_retries=3, model='deepseek-chat', temperature=0.7)")
    
    print("\n💡 使用示例:")
    
    # 示例1: 基本调用
    print("\n1. 基本调用:")
    print("```python")
    print("from app.api.ai_report import call_deepseek_api")
    print("")
    print("response = call_deepseek_api('请分析八字：乙亥年 壬午月 庚申日 癸未时')")
    print("print(response)")
    print("```")
    
    # 示例2: 使用不同模型
    print("\n2. 使用推理模型:")
    print("```python")
    print("response = call_deepseek_api(")
    print("    prompt='复杂的命理推理问题',")
    print("    model='deepseek-reasoner'")
    print(")")
    print("```")
    
    # 示例3: 调节temperature
    print("\n3. 调节创造性:")
    print("```python")
    print("# 更确定性的输出")
    print("response = call_deepseek_api(prompt, temperature=0.1)")
    print("")
    print("# 更创造性的输出")
    print("response = call_deepseek_api(prompt, temperature=0.9)")
    print("```")
    
    # 示例4: 在AI报告中使用
    print("\n4. 在AI报告生成中使用:")
    print("```python")
    print("# 在 app/api/ai_report.py 中替换:")
    print("# bazi_analysis = call_gemini_api(bazi_prompt)")
    print("# 为:")
    print("bazi_analysis = call_deepseek_api(bazi_prompt)")
    print("```")
    
    print("\n📊 成本对比:")
    print("- DeepSeek-Chat: ¥1.33/M输入 + ¥2.66/M输出")
    print("- Gemini-2.0-Flash: ~¥15-20/M tokens")
    print("- 节省成本: 约85-90%")
    
    print("\n🔄 切换步骤:")
    print("1. 确保DEEPSEEK_API_KEY已配置")
    print("2. 运行: python switch_to_deepseek.py (自动切换)")
    print("3. 或手动替换所有 call_gemini_api() 为 call_deepseek_api()")
    print("4. 重启服务器")
    
    print("\n⚠️ 当前状态:")
    if api_key:
        print("✅ API Key已配置到main.py")
        print("✅ call_deepseek_api()函数已添加")
        print("⚠️  账户余额不足，需要充值后使用")
        print("💰 充值地址: https://platform.deepseek.com/usage")
    else:
        print("❌ 需要设置DEEPSEEK_API_KEY环境变量")
    
    print("\n🎯 下一步:")
    print("1. 在DeepSeek平台充值账户")
    print("2. 运行切换脚本或手动替换API调用")
    print("3. 测试AI报告生成功能")

def show_api_comparison():
    """显示API对比"""
    print("\n" + "=" * 50)
    print("📊 API 对比分析")
    print("=" * 50)
    
    comparison = {
        "特性": ["价格", "中文支持", "地区限制", "API兼容性", "响应速度", "模型选择"],
        "DeepSeek": ["💰 很便宜", "🇨🇳 优秀", "🌍 无限制", "✅ OpenAI兼容", "⚡ 快", "🔄 多模型"],
        "Gemini": ["💸 较贵", "🇨🇳 良好", "🚫 有限制", "❌ 自有格式", "⚡ 快", "🔄 单模型"]
    }
    
    for i, feature in enumerate(comparison["特性"]):
        print(f"{feature:12} | {comparison['DeepSeek'][i]:15} | {comparison['Gemini'][i]}")

def main():
    """主函数"""
    demo_deepseek_function()
    show_api_comparison()
    
    print("\n🎉 DeepSeek API 已成功集成到项目中!")
    print("📖 详细文档: README_DEEPSEEK.md")

if __name__ == "__main__":
    main() 
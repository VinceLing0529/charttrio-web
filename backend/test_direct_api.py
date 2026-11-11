#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API Key直接写入的效果
验证不需要环境变量也能正常工作
"""

import os
import sys

# 清除环境变量以确保测试的是硬编码的API Key
if 'DEEPSEEK_API_KEY' in os.environ:
    del os.environ['DEEPSEEK_API_KEY']

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_hardcoded_api():
    """测试硬编码的API Key"""
    print("🔄 测试硬编码API Key")
    print("=" * 50)
    
    # 确认环境变量已清除
    env_key = os.getenv("DEEPSEEK_API_KEY", "")
    if env_key:
        print(f"⚠️  环境变量仍存在: {env_key[:8]}...")
    else:
        print("✅ 环境变量已清除，测试硬编码API Key")
    
    try:
        from app.api.ai_report import call_deepseek_api, DEEPSEEK_API_KEY
        print("✅ 成功导入DeepSeek API函数")
        print(f"✅ 硬编码API Key: {DEEPSEEK_API_KEY[:8]}...{DEEPSEEK_API_KEY[-8:]}")
        
        # 测试API调用
        print("🚀 测试API调用...")
        response = call_deepseek_api("请回复：硬编码API Key工作正常", temperature=0.1)
        print("✅ API调用成功")
        print(f"📄 响应: {response[:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    success = test_hardcoded_api()
    
    if success:
        print("\n🎉 硬编码API Key测试成功!")
        print("✅ 不需要设置环境变量")
        print("✅ API Key已直接写入ai_report.py")
        print("✅ 可以直接启动服务使用")
    else:
        print("\n❌ 测试失败")

if __name__ == "__main__":
    main() 
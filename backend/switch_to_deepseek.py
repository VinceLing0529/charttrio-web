#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
切换到DeepSeek API的示例脚本
展示如何将现有的AI报告系统从Gemini API切换到DeepSeek API
"""

import os
import re

def switch_api_calls():
    """将ai_report.py中的Gemini API调用切换为DeepSeek API调用"""
    
    file_path = "app/api/ai_report.py"
    
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ 文件 {file_path} 不存在")
        return False
    
    print("🔄 开始切换API调用...")
    
    # 备份原文件
    backup_path = file_path + ".gemini_backup"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 已备份原文件到: {backup_path}")
    
    # 替换API调用
    replacements = [
        # 替换函数调用
        (r'call_gemini_api\(', 'call_deepseek_api('),
        
        # 替换注释中的说明
        (r'# 调用Gemini API', '# 调用DeepSeek API'),
        (r'"""调用Gemini API', '"""调用DeepSeek API'),
        
        # 替换错误信息
        (r'Gemini API调用', 'DeepSeek API调用'),
        (r'gemini_analysis', 'deepseek_analysis'),
    ]
    
    modified_content = content
    changes_made = 0
    
    for pattern, replacement in replacements:
        old_content = modified_content
        modified_content = re.sub(pattern, replacement, modified_content)
        if old_content != modified_content:
            changes_made += len(re.findall(pattern, old_content))
    
    if changes_made > 0:
        # 写入修改后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"✅ 成功替换了 {changes_made} 处API调用")
        print("📝 主要修改:")
        print("  - call_gemini_api() → call_deepseek_api()")
        print("  - 相关注释和错误信息")
        
        return True
    else:
        print("ℹ️ 没有找到需要替换的内容")
        return False

def create_env_example():
    """创建环境变量配置示例文件"""
    
    env_content = """# DeepSeek API 配置
# 请将你的DeepSeek API Key填入下面的配置中

# DeepSeek API Key (必需)
# 获取地址: https://platform.deepseek.com/api_keys
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 可选：保留Gemini API Key作为备用
GEMINI_API_KEY=your_gemini_api_key_here

# 使用说明:
# 1. 将此文件重命名为 .env
# 2. 替换 your_deepseek_api_key_here 为你的真实API Key
# 3. 在项目根目录运行: pip install python-dotenv
# 4. 在main.py中添加: from dotenv import load_dotenv; load_dotenv()
"""
    
    with open(".env.example", 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ 已创建环境变量配置示例文件: .env.example")

def show_usage_instructions():
    """显示使用说明"""
    
    instructions = """
🚀 DeepSeek API 集成完成!

📋 接下来的步骤:

1. 获取DeepSeek API Key:
   - 访问: https://platform.deepseek.com/api_keys
   - 注册账号并创建API Key

2. 设置环境变量:
   Windows PowerShell:
   $env:DEEPSEEK_API_KEY="your_api_key_here"
   
   Windows CMD:
   set DEEPSEEK_API_KEY=your_api_key_here
   
   Linux/Mac:
   export DEEPSEEK_API_KEY=your_api_key_here

3. 测试API调用:
   cd lifeinsight-web/backend
   python deepseek_example.py

4. 启动服务:
   python -m uvicorn app.main:app --reload

💡 优势对比:

DeepSeek vs Gemini:
✅ 价格更便宜 (约为Gemini的1/10)
✅ 中文支持更好
✅ 无地区限制
✅ API格式兼容OpenAI
✅ 响应速度快

📊 价格对比 (每1M tokens):
- DeepSeek-Chat: ¥1.33 (输入) / ¥2.66 (输出)
- Gemini-2.0-Flash: ~¥15-20

🔧 如果需要回滚到Gemini:
1. 恢复备份文件: cp app/api/ai_report.py.gemini_backup app/api/ai_report.py
2. 设置GEMINI_API_KEY环境变量

🆘 常见问题:
- API Key错误: 检查环境变量设置
- 网络超时: 检查网络连接
- 格式错误: 确保prompt格式正确
"""
    
    print(instructions)

def main():
    """主函数"""
    print("🔄 DeepSeek API 集成工具")
    print("=" * 50)
    
    # 检查当前目录
    if not os.path.exists("app/api/ai_report.py"):
        print("❌ 请在lifeinsight-web/backend目录下运行此脚本")
        return
    
    # 执行切换
    print("1. 切换API调用...")
    success = switch_api_calls()
    
    print("\n2. 创建环境变量配置示例...")
    create_env_example()
    
    print("\n3. 显示使用说明...")
    show_usage_instructions()
    
    if success:
        print("\n🎉 DeepSeek API 集成完成!")
        print("⚠️  请确保设置DEEPSEEK_API_KEY环境变量后再使用")
    else:
        print("\n⚠️  集成过程中遇到问题，请检查文件路径和权限")

if __name__ == "__main__":
    main() 
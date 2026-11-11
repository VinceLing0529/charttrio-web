# DeepSeek API 集成指南

本文档介绍如何在 lifeinsight-web 项目中集成和使用 DeepSeek API。

## 🚀 快速开始

### 1. 获取 API Key

1. 访问 [DeepSeek Platform](https://platform.deepseek.com/api_keys)
2. 注册账号并登录
3. 创建新的 API Key
4. 复制 API Key 备用

### 2. 配置环境变量

#### Windows PowerShell
```powershell
$env:DEEPSEEK_API_KEY="your_api_key_here"
```

#### Windows CMD
```cmd
set DEEPSEEK_API_KEY=your_api_key_here
```

#### Linux/Mac
```bash
export DEEPSEEK_API_KEY=your_api_key_here
```

### 3. 测试 API 连接

```bash
cd lifeinsight-web/backend
python test_deepseek.py
```

## 📋 API 功能说明

### call_deepseek_api() 函数

已在 `app/api/ai_report.py` 中添加了 DeepSeek API 调用函数：

```python
def call_deepseek_api(prompt_text, max_retries=3, model="deepseek-chat", temperature=0.7):
    """调用DeepSeek API，支持重试机制"""
    # 函数实现...
```

#### 参数说明：
- `prompt_text`: 输入的提示文本
- `max_retries`: 最大重试次数（默认3次）
- `model`: 使用的模型（默认 "deepseek-chat"）
- `temperature`: 温度参数，控制输出随机性（0.0-1.0）

#### 支持的模型：
- `deepseek-chat`: 通用对话模型（推荐）
- `deepseek-reasoner`: 推理专用模型

## 🔄 从 Gemini 切换到 DeepSeek

### 自动切换脚本

运行自动切换脚本：

```bash
cd lifeinsight-web/backend
python switch_to_deepseek.py
```

此脚本会：
1. 备份原始的 `ai_report.py` 文件
2. 自动替换所有 `call_gemini_api()` 为 `call_deepseek_api()`
3. 创建环境变量配置示例文件

### 手动切换

在 `app/api/ai_report.py` 中找到所有 `call_gemini_api()` 调用，替换为 `call_deepseek_api()`：

```python
# 原来的代码
bazi_analysis = call_gemini_api(bazi_prompt)

# 替换为
bazi_analysis = call_deepseek_api(bazi_prompt)
```

## 💡 使用示例

### 基本对话
```python
from app.api.ai_report import call_deepseek_api

response = call_deepseek_api("你好，请介绍一下DeepSeek模型。")
print(response)
```

### 命理分析
```python
prompt = """
请分析以下八字信息：
八字四柱：乙亥年 壬午月 庚申日 癸未时
日主：庚金
身强身弱：身弱

请分析此人的性格特点和事业发展方向。
"""

response = call_deepseek_api(prompt)
print(response)
```

### JSON 格式输出
```python
prompt = """
请分析八字"乙亥年 壬午月 庚申日 癸未时"，并以JSON格式返回：
{
  "性格特点": "性格描述",
  "事业方向": "事业建议",
  "财运": "财运分析"
}
"""

response = call_deepseek_api(prompt)
import json
data = json.loads(response)
```

### 使用不同模型
```python
# 使用推理模型
response = call_deepseek_api(prompt, model="deepseek-reasoner")

# 调整温度参数
response = call_deepseek_api(prompt, temperature=0.1)  # 更确定性的输出
response = call_deepseek_api(prompt, temperature=0.9)  # 更创造性的输出
```

## 📊 价格对比

| 模型 | 输入价格 (¥/1M tokens) | 输出价格 (¥/1M tokens) |
|------|------------------------|------------------------|
| DeepSeek-Chat | 1.33 | 2.66 |
| DeepSeek-Reasoner | 1.33 | 2.66 |
| Gemini-2.0-Flash | ~15-20 | ~15-20 |

**DeepSeek 比 Gemini 便宜约 85-90%！**

## ✅ DeepSeek vs Gemini 优势

### ✅ DeepSeek 优势
- **价格便宜**: 约为 Gemini 的 1/10
- **中文支持**: 专门优化的中文能力
- **无地区限制**: 全球可用，无需代理
- **API 兼容**: 与 OpenAI API 格式兼容
- **响应速度**: 通常比 Gemini 更快
- **模型选择**: 提供专门的推理模型

### ⚠️ 注意事项
- 需要注册 DeepSeek 账号
- 新模型，长期稳定性待观察
- 某些特定任务可能不如 Gemini 专业

## 🔧 故障排除

### API Key 错误
```
错误: DeepSeek API Key未配置
解决: 检查环境变量 DEEPSEEK_API_KEY 是否正确设置
```

### 网络超时
```
错误: API调用多次超时
解决: 检查网络连接，或增加 timeout 参数
```

### JSON 解析失败
```
错误: JSON解析失败
解决: 检查 prompt 格式，确保要求明确的 JSON 输出
```

### 模型不存在
```
错误: 模型不存在
解决: 确认使用正确的模型名称（deepseek-chat 或 deepseek-reasoner）
```

## 🔄 回滚到 Gemini

如果需要回滚到 Gemini API：

```bash
# 恢复备份文件
cp app/api/ai_report.py.gemini_backup app/api/ai_report.py

# 设置 Gemini API Key
export GEMINI_API_KEY=your_gemini_api_key
```

## 📝 最佳实践

1. **错误处理**: 始终使用 try-catch 包装 API 调用
2. **重试机制**: 利用内置的重试机制处理临时错误
3. **温度调节**: 根据需求调整 temperature 参数
4. **模型选择**: 复杂推理任务使用 deepseek-reasoner
5. **成本控制**: 监控 token 使用量，控制成本

## 🆘 技术支持

- [DeepSeek 官方文档](https://api-docs.deepseek.com/zh-cn/)
- [DeepSeek 社区](https://discord.gg/deepseek)
- [问题反馈](https://github.com/deepseek-ai/deepseek-coder/issues)

---

**🎉 现在你可以使用 DeepSeek API 为你的命理网站提供更经济高效的 AI 分析服务了！** 
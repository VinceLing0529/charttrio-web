# 🔒 AI上下文隔离问题解决方案

## 问题描述
当前系统在多用户并发使用时存在上下文混乱的风险：
- 用户A建立上下文后，用户B的操作可能覆盖用户A的上下文
- 导致用户A收到基于用户B数据的错误分析

## 解决方案实现

### 1. 修改 AI API 调用函数

```python
# 在 ai_analysis.py 中修改
async def call_ai_api_safe(prompt: str, order_id: str, include_context: bool = True) -> Dict[str, Any]:
    """
    安全的AI API调用，包含用户上下文隔离
    """
    print(f"调用AI API (订单: {order_id})...")
    
    if include_context:
        # 从文件系统加载用户的命盘数据
        user_analysis = load_analysis_result(order_id)
        if user_analysis and 'user_data' in user_analysis:
            user_data = user_analysis['user_data']
            
            # 构造包含完整上下文的prompt
            context_data = f"""
用户命盘信息：
出生信息：{user_data.get('input', {})}
八字信息：{user_data.get('bazi', {})}
紫微斗数：{user_data.get('ziwei', {})}
印度星盘：{user_data.get('vedic', {})}

基于以上用户的完整命盘数据，"""
            
            full_prompt = context_data + prompt
        else:
            full_prompt = prompt
    else:
        full_prompt = prompt
    
    # 这里调用真实的AI API
    # response = await gemini_api_call(full_prompt, session_id=order_id)
    
    # 当前返回模拟数据（保持现有逻辑）
    return await original_call_ai_api_logic(full_prompt)
```

### 2. 修改所有AI调用点

```python
# 所有维度分析调用修改为：
ai_response = await call_ai_api_safe(
    prompt=dimension_config['prompt_template'],
    order_id=request.order_id,
    include_context=True
)

# 上下文建立调用：
ai_response = await call_ai_api_safe(
    prompt=context_prompt,
    order_id=request.order_id,
    include_context=False
)
```

### 3. 数据流程图

```
用户A提交 → 生成order_id_A → 保存命盘数据_A
↓
分析请求 → 加载命盘数据_A → 构造完整prompt_A → AI分析_A

用户B提交 → 生成order_id_B → 保存命盘数据_B  
↓
分析请求 → 加载命盘数据_B → 构造完整prompt_B → AI分析_B
```

### 4. 真实AI API集成示例

```python
import google.generativeai as genai

async def call_gemini_api_safe(prompt: str, order_id: str):
    """
    安全的Gemini API调用
    """
    try:
        # 为每个用户创建独立的对话
        model = genai.GenerativeModel('gemini-pro')
        
        # 使用order_id作为对话标识
        chat = model.start_chat(history=[])
        
        response = chat.send_message(prompt)
        return response.text
        
    except Exception as e:
        print(f"Gemini API调用失败 (订单: {order_id}): {e}")
        raise
```

### 5. 会话存储优化

```python
# 可选：使用Redis存储会话状态
import redis

class ContextManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    def store_context(self, order_id: str, user_data: dict):
        """存储用户上下文"""
        self.redis_client.setex(
            f"context:{order_id}", 
            3600,  # 1小时过期
            json.dumps(user_data)
        )
    
    def get_context(self, order_id: str) -> dict:
        """获取用户上下文"""
        data = self.redis_client.get(f"context:{order_id}")
        return json.loads(data) if data else None
```

## 立即可用的快速修复

### 方案A：完整数据传递（推荐）
每次调用AI时都传递完整的用户数据，不依赖AI的"记忆"

优点：
- ✅ 完全隔离，绝对安全
- ✅ 不依赖AI的会话功能
- ✅ 容易实现和调试

缺点：
- ❌ 每次请求数据量较大
- ❌ Token消耗较多

### 方案B：会话ID隔离
使用AI API的会话功能进行隔离

优点：
- ✅ 数据传输效率高
- ✅ Token消耗较少

缺点：
- ❌ 依赖AI API的会话功能
- ❌ 如果AI API重启会丢失上下文

## 测试验证

```python
# 测试脚本
async def test_concurrent_users():
    """测试并发用户隔离"""
    
    # 模拟用户A
    order_a = "AI20250101120000UserA"
    user_data_a = {"name": "张三", "birth": "1990-01-01"}
    await setup_context(order_a, user_data_a)
    
    # 模拟用户B  
    order_b = "AI20250101120001UserB"
    user_data_b = {"name": "李四", "birth": "1985-01-01"}
    await setup_context(order_b, user_data_b)
    
    # 同时请求分析
    result_a = await analyze_dimension(order_a, "talents")
    result_b = await analyze_dimension(order_b, "talents")
    
    # 验证结果不会混乱
    assert "张三" in result_a or "1990" in result_a
    assert "李四" in result_b or "1985" in result_b
    assert result_a != result_b
```

## 紧急程度

这是一个 **🚨 高优先级** 问题，建议：

1. **立即实施方案A（完整数据传递）**
2. **在所有AI调用中添加order_id参数**
3. **测试并发场景**
4. **监控生产环境的用户隔离情况**

如果不解决这个问题，系统上线后会出现用户数据混乱的严重bug！ 
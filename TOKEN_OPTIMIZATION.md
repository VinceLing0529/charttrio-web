# Token使用量优化方案

## 问题描述
在AI分析功能中添加context测试功能后，每个prompt都增加了约60-80个中文字符的测试语句，导致token使用量大幅增加（约20-30%）。

## 优化方案

### 1. 可控制的测试模式
- 添加了全局配置 `ENABLE_CONTEXT_TEST`
- 默认值：`False`（生产环境使用优化后的prompt）
- 可通过API动态切换

### 2. Token使用量对比

#### 测试模式启用时：
```text
每个分析维度额外增加：
"请问你是否能够读取到我之前提供的完整命盘信息（包括八字、紫微斗数、印度星盘的详细数据）？

如果你无法读取到我的命盘数据，请回答"否"。

如果你可以读取到我的命盘数据，"
```
- 约80个中文字符 × 5个维度 = 400个额外字符
- 按照1个中文字符≈1.5 token计算 = 约600个额外token

#### 测试模式禁用时：
```text
直接使用优化后的prompt：
"请基于命盘信息分析..."
```
- 每个分析维度节省约80个字符
- 5个维度总共节省约600个token

### 3. API控制端点

#### 切换测试模式
```http
POST /test/toggle-context-test
Content-Type: application/json

{
    "enable": false  // true启用，false禁用
}
```

#### 查看当前状态
```http
GET /test/context-test-status
```

### 4. 使用建议

#### 开发测试阶段：
```python
# 启用测试模式，验证context功能
ENABLE_CONTEXT_TEST = True
```

#### 生产环境：
```python
# 禁用测试模式，最小化token使用
ENABLE_CONTEXT_TEST = False
```

### 5. 预期收益
- 生产环境下token使用量减少20-30%
- 保持完整的context测试能力
- 可随时切换模式进行调试

## 实施状态
✅ 已完成优化实施  
✅ 默认使用最优化模式  
✅ 提供API控制接口  
✅ 保持向后兼容性 
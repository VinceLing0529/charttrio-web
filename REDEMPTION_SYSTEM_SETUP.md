# 兑换码系统安装和启动说明

## 系统概述

兑换码系统为AI报告生成功能提供付费验证机制，包含以下组件：

1. **前端兑换码悬浮窗** - 用户输入兑换码验证
2. **后端兑换码API** - 验证和管理兑换码
3. **Redis数据库** - 存储兑换码数据
4. **兑换码管理页面** - 管理员生成和管理兑换码

## 安装步骤

### 1. 安装Redis

#### Windows
```bash
# 下载Redis for Windows
# 访问: https://github.com/microsoftarchive/redis/releases
# 下载最新版本的 .msi 文件并安装

# 或者使用Chocolatey
choco install redis-64

# 启动Redis服务
redis-server
```

#### macOS
```bash
# 使用Homebrew安装
brew install redis

# 启动Redis服务
brew services start redis
```

#### Linux (Ubuntu/Debian)
```bash
# 安装Redis
sudo apt update
sudo apt install redis-server

# 启动Redis服务
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 2. 安装Python依赖

```bash
# 进入后端目录
cd lifeinsight-web/backend

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装Redis依赖
pip install redis>=4.5.0

# 或者重新安装所有依赖
pip install -r requirements.txt
```

### 3. 验证Redis连接

```bash
# 测试Redis连接
redis-cli ping
# 应该返回: PONG
```

## 启动系统

### 1. 启动后端服务

```bash
# 进入后端目录
cd lifeinsight-web/backend

# 激活虚拟环境
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 启动后端服务
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. 启动前端服务

```bash
# 进入前端目录
cd lifeinsight-web/frontend

# 启动前端服务
npm start
```

## 使用说明

### 1. 生成兑换码

访问兑换码管理页面：`http://localhost:3000/redemption-admin`

- 设置生成数量（1-100个）
- 设置有效期（1-365天）
- 点击"生成兑换码"

### 2. 用户使用兑换码

1. 用户完成命盘分析后，点击"立即获取完整报告"
2. 弹出兑换码输入悬浮窗
3. 用户输入兑换码并点击"开始探索"
4. 验证成功后自动跳转到AI报告生成页面

### 3. 兑换码管理

在兑换码管理页面可以：
- 查看所有兑换码列表
- 查看使用统计信息
- 复制兑换码
- 删除兑换码
- 查看兑换码状态（可用/已使用/已过期）

## API接口

### 验证兑换码
```
POST http://localhost:8000/api/redemption-codes/verify
Content-Type: application/json

{
    "code": "LIFE12345678"
}
```

### 生成兑换码
```
POST http://localhost:8000/api/redemption-codes/generate
Content-Type: application/json

{
    "quantity": 10,
    "expires_in_days": 30
}
```

### 获取兑换码列表
```
GET http://localhost:8000/api/redemption-codes/list
```

### 获取统计信息
```
GET http://localhost:8000/api/redemption-codes/stats
```

### 删除兑换码
```
DELETE http://localhost:8000/api/redemption-codes/{code}
```

## 兑换码格式

- 格式：`LIFE` + 8位随机大写字母数字组合
- 示例：`LIFE1A2B3C4D`
- 长度：12位字符

## 数据存储

兑换码数据存储在Redis中：
- Key格式：`redemption_code:{code}`
- 数据格式：JSON字符串
- 过期时间：根据设置的有效期自动过期

## 故障排除

### Redis连接失败
```bash
# 检查Redis服务状态
redis-cli ping

# 如果返回错误，重启Redis服务
# Windows: 重启Redis服务
# macOS: brew services restart redis
# Linux: sudo systemctl restart redis-server
```

### 后端启动失败
```bash
# 检查依赖是否安装完整
pip list | grep redis

# 重新安装依赖
pip install -r requirements.txt
```

### 前端无法连接后端
```bash
# 检查后端服务是否正常运行
curl http://localhost:8000/health

# 检查CORS配置是否正确
```

## 安全注意事项

1. **兑换码安全性**：兑换码使用UUID生成，具有足够的随机性
2. **一次性使用**：每个兑换码只能使用一次
3. **自动过期**：兑换码会根据设置的有效期自动过期
4. **Redis安全**：建议在生产环境中配置Redis密码和网络访问限制

## 扩展功能

### 支付集成
可以在`handlePurchase`函数中集成第三方支付API：
- 支付宝
- 微信支付
- Stripe
- PayPal

### 批量操作
可以添加批量生成、批量删除等管理功能

### 使用统计
可以添加更详细的使用统计和报表功能 
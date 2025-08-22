# 企业微信消息接收服务

这是一个专门用于接收企业微信自定义应用推送消息的简化服务。

## 功能特性

### 🚀 支持的消息类型

- ✅ **文本消息 (text)**: 接收和发送纯文本消息，支持自定义业务逻辑
- ✅ **图片消息 (image)**: 接收图片消息，支持图片 URL 和媒体 ID 获取
- ✅ **语音消息 (voice)**: 接收语音消息，支持多种语音格式（amr 等）
- ✅ **位置消息 (location)**: 接收位置信息，支持地理位置坐标和标签
- ✅ **事件消息 (event)**: 处理各种企业微信事件（订阅/取消订阅等）

### 📤 支持的消息发送

- ✅ **文本消息**: 支持纯文本发送
- ✅ **Markdown 消息**: 支持富文本格式，超过 1000 字符自动生成 PDF
- ✅ **文件消息**: 支持文件上传和发送
- ✅ **位置消息**: 支持地理位置信息发送

### 🔧 企业微信 API 支持

- ✅ **用户管理**: 获取用户详细信息
- ✅ **部门管理**: 获取部门信息和层级关系
- ✅ **媒体文件**: 支持文件上传、下载和管理
- ✅ **访问令牌**: 自动获取和管理访问令牌，支持过期刷新

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# 企业微信配置
WECOM_CORP_ID=你的企业ID
WECOM_AGENT_ID=你的应用ID
WECOM_AGENT_SECRET=你的应用密钥
WECOM_TOKEN=你的Token
WECOM_ENCODING_AES_KEY=你的EncodingAESKey

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

### 3. 启动服务

```bash
python start_server.py
```

或者使用 uvicorn：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. 配置企业微信

在企业微信管理后台配置回调 URL：

- **回调 URL**: `http://你的域名:8000/wechat/callback`
- **Token**: 与 `.env` 中的 `WECOM_TOKEN` 一致
- **EncodingAESKey**: 与 `.env` 中的 `WECOM_ENCODING_AES_KEY` 一致

### 5. 生产环境部署

使用提供的生产环境脚本：

```bash
# 启动服务
./start_app_prod.sh start

# 查看状态
./start_app_prod.sh status

# 查看日志
./start_app_prod.sh logs

# 停止服务
./start_app_prod.sh stop

# 重启服务
./start_app_prod.sh restart
```

生产环境使用 Gunicorn + Uvicorn Worker，提供更好的性能和稳定性。

## API 接口

### 1. 企业微信回调接口

- **POST** `/wechat/callback` - 接收企业微信推送的消息

### 2. 企业微信验证接口

- **GET** `/wechat/verify` - 验证回调 URL 的有效性

### 3. 健康检查接口

- **GET** `/health` - 服务健康状态检查

## 消息处理

### 📝 消息类型详解

#### 1. 文本消息 (text)

- **接收字段**: content, from_user, msg_id, create_time
- **处理方式**: 支持自定义业务逻辑，可调用 AI 服务、查询数据库等
- **回复方式**: 支持文本和 Markdown 格式回复

#### 2. 图片消息 (image)

- **接收字段**: pic_url, media_id, from_user, msg_id, create_time
- **处理方式**: 支持图片 URL 获取和媒体文件下载
- **扩展功能**: 可集成图片识别、图片分析等 AI 服务

#### 3. 语音消息 (voice)

- **接收字段**: voice_url, voice_format, media_id, from_user, msg_id, create_time
- **支持格式**: amr 等企业微信支持的语音格式
- **处理方式**: 支持语音文件下载，可集成语音转文字服务

#### 4. 位置消息 (location)

- **接收字段**: latitude, longitude, scale, label, from_user, msg_id, create_time
- **处理方式**: 支持地理位置坐标和标签信息处理
- **扩展功能**: 可集成地图服务、位置分析等

#### 5. 事件消息 (event)

- **接收字段**: event, from_user, create_time, agent_id
- **事件类型**: 订阅、取消订阅等企业微信事件
- **处理方式**: 支持事件驱动的业务逻辑处理

## 使用示例

### 🚀 基本消息处理

```python
from app.utils.wecom import WeComService

wecom_service = WeComService()

# 发送文本消息
await wecom_service.send_text_message("user123", "Hello World!")

# 发送Markdown消息
markdown_content = "**粗体** *斜体* `代码`"
await wecom_service.send_markdown_message("user123", markdown_content)

# 发送位置消息
await wecom_service.send_location_message("user123", 39.9042, 116.4074, "北京天安门")
```

### 📝 消息解析示例

```python
# 解析企业微信消息
message = wecom_service.parse_message(body, msg_signature, timestamp, nonce)

# 根据消息类型处理
if message["msg_type"] == "text":
    content = message["content"]
    user_id = message["from_user"]
    # 处理文本消息...
elif message["msg_type"] == "voice":
    voice_format = message["voice_format"]
    media_id = message["media_id"]
    # 处理语音消息...
```

### 🔧 API 调用示例

```python
# 获取用户信息
user_info = wecom_service.get_user_info("user123")
print(f"用户名: {user_info.get('name')}")

# 获取部门信息
dept_info = wecom_service.get_department_info(1)
print(f"部门名: {dept_info.get('name')}")

# 下载媒体文件
success = await wecom_service.download_media_file("media_id", "local_path")
```

## 自定义业务逻辑

在 `app/api/wechat.py` 文件中，你可以看到多个 `TODO` 注释，这些地方可以添加你的具体业务逻辑：

```python
async def _handle_text_message(message: dict):
    """处理文本消息"""
    try:
        user_id = message.get("from_user")
        content = message.get("content", "").strip()

        # TODO: 在这里添加你的业务逻辑处理
        # 例如：调用AI服务、查询数据库、调用其他API等

        # 发送回复消息
        reply_content = f"收到你的消息：{content}\n\n这是自动回复，具体业务逻辑待实现。"
        await wecom_service.send_text_message(user_id, reply_content)

    except Exception as e:
        logger.error(f"处理文本消息失败: {e}")
```

## 项目结构

```
app/
├── api/
│   ├── wechat.py          # 企业微信API接口和消息处理
│   └── health.py          # 健康检查和根路径接口
├── core/
│   ├── config.py          # 配置管理（环境变量、应用设置）
│   ├── error_handler.py   # 全局错误处理中间件
│   └── logging.py         # 日志配置和格式化
├── utils/
│   ├── wecom.py           # 企业微信服务类（消息处理、API调用）
│   ├── crypto.py          # 企业微信消息加密解密
│   └── text_to_pdf.py     # PDF生成工具（支持中文、Markdown）
├── models/                 # 数据模型定义
├── services/               # 业务服务层
├── tools/                  # 工具函数
└── main.py                # FastAPI主应用入口
```

### 📁 核心文件说明

- **`wechat.py`**: 企业微信消息接收和处理的入口，支持多种消息类型
- **`wecom.py`**: 企业微信 API 服务类，提供完整的消息处理、发送、用户管理等功能
- **`crypto.py`**: 企业微信消息加密解密，确保消息安全
- **`text_to_pdf.py`**: PDF 生成工具，支持中文字体和 Markdown 语法，用于长消息处理

## 依赖说明

### 📦 核心依赖

```txt
fastapi==0.115.9          # Web框架
uvicorn[standard]==0.34.3 # ASGI服务器
gunicorn==23.0.0          # WSGI服务器（生产环境）
httpx==0.28.1             # HTTP客户端
pydantic-settings==2.10.1 # 配置管理
python-multipart==0.0.20  # 文件上传支持
reportlab==4.1.0          # PDF生成（支持中文）
```

### 🔄 功能模块

- ✅ **企业微信集成**: 完整的消息接收、发送、API 调用功能
- ✅ **消息加密**: 支持企业微信消息加密解密
- ✅ **PDF 生成**: 支持长消息转 PDF，支持中文字体和 Markdown
- ❌ **Redis 缓存**: 已移除，简化部署
- ✅ **文件管理**: 支持媒体文件上传、下载、发送

## 注意事项

1. **安全性**: 已实现企业微信消息加密解密功能，确保消息安全
2. **错误处理**: 所有接口都有完善的错误处理和重试机制
3. **日志**: 服务会记录详细的访问日志和错误日志，支持日志轮转
4. **性能**: 消息处理采用异步方式，支持长消息自动分段和 PDF 生成
5. **字体支持**: PDF 生成支持中文字体，自动检测系统字体

## 开发计划

### 🚀 已完成功能

- [x] ✅ 企业微信消息加密/解密功能
- [x] ✅ 支持多种消息类型（文本、图片、语音、位置、事件）
- [x] ✅ 消息自动分段和 PDF 生成
- [x] ✅ 文件上传下载和发送
- [x] ✅ 用户和部门信息管理
- [x] ✅ 完善的错误处理和重试机制

### 🔮 计划功能

- [ ] 📊 添加消息类型过滤器
- [ ] 📱 支持更多消息类型（视频、文件、链接、名片、小程序）
- [ ] 💾 添加消息持久化存储
- [ ] 🎯 实现消息重试和队列机制
- [ ] 🖥️ 添加管理后台界面
- [ ] 📈 添加消息统计和分析功能
- [ ] 🔐 增强安全性和权限控制
- [ ] 🌐 支持多租户和企业配置

## 许可证

MIT License

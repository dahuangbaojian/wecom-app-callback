# 企业微信消息接收服务

这是一个专门用于接收企业微信自定义应用推送消息的简化服务。

## 功能特性

- ✅ 接收企业微信文本消息
- ✅ 接收企业微信语音消息
- ✅ 接收企业微信图片消息
- ✅ 接收企业微信事件消息（订阅/取消订阅）
- ✅ 自动回复消息
- ✅ 支持企业微信服务器配置验证

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

## API 接口

### 1. 企业微信回调接口

- **POST** `/wechat/callback` - 接收企业微信推送的消息

### 2. 企业微信验证接口

- **GET** `/wechat/verify` - 验证回调 URL 的有效性

### 3. 健康检查接口

- **GET** `/health` - 服务健康状态检查

## 消息处理

目前支持的消息类型：

- **文本消息**: 自动回复收到的文本内容
- **语音消息**: 提示收到语音消息（处理逻辑待实现）
- **图片消息**: 提示收到图片消息（处理逻辑待实现）
- **事件消息**: 处理订阅/取消订阅事件

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
│   └── wechat.py          # 企业微信API接口
├── core/
│   ├── config.py          # 配置管理
│   ├── error_handler.py   # 错误处理
│   └── logging.py         # 日志配置
├── utils/
│   └── wecom.py           # 企业微信服务类
└── main.py                # 主应用入口
```

## 注意事项

1. **安全性**: 当前版本的消息解密功能待实现，建议在生产环境中启用加密
2. **错误处理**: 所有接口都有基本的错误处理，但可能需要根据具体需求调整
3. **日志**: 服务会记录详细的访问日志和错误日志
4. **性能**: 消息处理采用异步方式，不会阻塞响应

## 开发计划

- [ ] 实现消息加密/解密功能
- [ ] 添加消息类型过滤器
- [ ] 支持更多消息类型（文件、位置等）
- [ ] 添加消息持久化存储
- [ ] 实现消息重试机制
- [ ] 添加管理后台界面

## 许可证

MIT License

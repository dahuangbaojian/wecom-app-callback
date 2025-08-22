#!/usr/bin/env python3
"""
企业微信消息接收服务启动脚本
"""

import uvicorn
from app.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()

    print(f"🚀 启动企业微信消息接收服务...")
    print(f"📍 服务地址: http://{settings.HOST}:{settings.PORT}")
    print(f"🔧 调试模式: {settings.DEBUG}")
    print(f"📝 日志级别: {settings.LOG_LEVEL}")

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )

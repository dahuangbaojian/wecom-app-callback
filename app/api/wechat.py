import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, Request, Response

from ..core.error_handler import error_handler
from ..utils.wecom import WeComService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wechat", tags=["企业微信"])

# 创建企业微信服务单例
wecom_service = WeComService()


@router.post("/callback")
@error_handler("企业微信回调处理")
async def handle_callback(request: Request):
    """
    处理企业微信回调消息

    Args:
        request: FastAPI请求对象

    Returns:
        企业微信响应
    """
    try:
        # 获取请求体
        body = await request.body()

        # 获取URL参数
        query_params = dict(request.query_params)
        msg_signature = query_params.get("msg_signature", "")
        timestamp = query_params.get("timestamp", "")
        nonce = query_params.get("nonce", "")

        logger.debug(
            f"企业微信回调参数: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}"
        )

        # 立即返回成功响应，避免企业微信重复推送
        # 异步处理消息，不阻塞响应
        asyncio.create_task(
            _process_message_async(body, msg_signature, timestamp, nonce)
        )

        return Response(content="success", media_type="text/plain")

    except Exception as e:
        logger.error(f"企业微信回调处理失败: {e}")
        return Response(content="success", media_type="text/plain")


async def _process_message_async(
    body: bytes, msg_signature: str, timestamp: str, nonce: str
):
    """异步处理企业微信消息"""
    try:
        # 解析企业微信消息
        message = wecom_service.parse_message(body, msg_signature, timestamp, nonce)

        if not message:
            logger.warning("无法解析企业微信消息")
            return

        # 获取用户信息
        user_id = message.get("from_user")
        msg_type = message.get("msg_type")

        logger.info(f"收到企业微信消息: 类型={msg_type}, 用户={user_id}")

        # 根据消息类型处理
        if msg_type == "text":
            await _handle_text_message(message)
        elif msg_type == "voice":
            await _handle_voice_message(message)
        elif msg_type == "image":
            await _handle_image_message(message)
        elif msg_type == "event":
            await _handle_event_message(message)
        else:
            logger.info(f"暂不支持的消息类型: {msg_type}")

    except Exception as e:
        logger.error(f"异步处理企业微信消息失败: {e}")


async def _handle_text_message(message: dict):
    """处理文本消息"""
    try:
        user_id = message.get("from_user")
        content = message.get("content", "").strip()

        if not content:
            logger.warning("收到空文本消息", extra={"user_id": user_id})
            return

        logger.info(f"处理文本消息: {content}", extra={"user_id": user_id})

        # TODO: 在这里添加你的业务逻辑处理
        # 例如：调用AI服务、查询数据库、调用其他API等

        # 发送回复消息
        reply_content = f"收到你的消息：{content}\n\n这是自动回复，具体业务逻辑待实现。"
        await wecom_service.send_text_message(user_id, reply_content)

        logger.debug("文本消息处理完成", extra={"user_id": user_id})

    except Exception as e:
        logger.error(
            f"处理文本消息失败: {e}", extra={"user_id": message.get("from_user")}
        )


async def _handle_voice_message(message: dict):
    """处理语音消息"""
    try:
        user_id = message.get("from_user")
        voice_format = message.get("voice_format", "amr")

        logger.info(f"处理语音消息，格式: {voice_format}", extra={"user_id": user_id})

        # TODO: 在这里添加语音处理逻辑
        # 例如：语音转文字、语音识别等

        reply_content = f"收到语音消息，格式：{voice_format}\n\n语音处理功能待实现。"
        await wecom_service.send_text_message(user_id, reply_content)

        logger.debug("语音消息处理完成", extra={"user_id": user_id})

    except Exception as e:
        logger.error(
            f"处理语音消息失败: {e}", extra={"user_id": message.get("from_user")}
        )


async def _handle_image_message(message: dict):
    """处理图片消息"""
    try:
        user_id = message.get("from_user")
        pic_url = message.get("pic_url")

        logger.info(f"处理图片消息: {pic_url}", extra={"user_id": user_id})

        # TODO: 在这里添加图片处理逻辑
        # 例如：图片识别、图片分析等

        reply_content = "收到图片消息，图片处理功能待实现。"
        await wecom_service.send_text_message(user_id, reply_content)

        logger.debug("图片消息处理完成", extra={"user_id": user_id})

    except Exception as e:
        logger.error(
            f"处理图片消息失败: {e}", extra={"user_id": message.get("from_user")}
        )


async def _handle_event_message(message: dict):
    """处理事件消息"""
    try:
        user_id = message.get("from_user")
        event = message.get("event")

        logger.info(f"处理事件消息: {event}", extra={"user_id": user_id})

        if event == "subscribe":
            # 订阅事件 - 发送欢迎消息
            welcome_message = """🎉 你好，欢迎使用企业微信消息接收服务！

目前支持的功能：
- 接收文本消息
- 接收语音消息  
- 接收图片消息
- 自动回复

具体业务逻辑待实现，请查看代码中的TODO注释。"""

            await wecom_service.send_text_message(user_id, welcome_message)
            logger.info("发送订阅欢迎消息完成", extra={"user_id": user_id})

        elif event == "unsubscribe":
            # 取消订阅事件
            logger.info("用户取消订阅", extra={"user_id": user_id})

        else:
            # 其他事件类型
            logger.info(f"暂不支持的事件类型: {event}", extra={"user_id": user_id})

    except Exception as e:
        logger.error(
            f"处理事件消息失败: {e}", extra={"user_id": message.get("from_user")}
        )


@router.get("/verify")
async def verify_url(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    """
    企业微信服务器配置验证接口

    用于验证回调URL的有效性
    """
    try:
        logger.info(
            f"验证回调URL: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}"
        )

        # 验证URL
        decrypted = wecom_service.verify_url(msg_signature, timestamp, nonce, echostr)

        logger.info("URL验证成功")
        return Response(content=decrypted, media_type="text/plain")

    except Exception as e:
        logger.error(f"URL验证失败: {e}")
        return Response(content="验证失败", media_type="text/plain", status_code=400)

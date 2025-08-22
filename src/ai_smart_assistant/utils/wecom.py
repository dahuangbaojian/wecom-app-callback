import json
import logging
import time
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, Dict

import httpx

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class WeComService:
    def __init__(self):
        settings = get_settings()
        self.corp_id = settings.WECOM_CORP_ID
        self.agent_id = settings.WECOM_AGENT_ID
        self.secret = settings.WECOM_AGENT_SECRET
        self.token = settings.WECOM_TOKEN
        self.encoding_aes_key = settings.WECOM_ENCODING_AES_KEY
        self.api_url = "https://qyapi.weixin.qq.com/cgi-bin"
        
        # 简单的access_token缓存
        self.access_token = None
        self.access_token_expires = 0

    def verify_url(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> str:
        """验证回调URL"""
        try:
            logger.debug(
                f"开始验证URL: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}"
            )
            echostr = urllib.parse.unquote(echostr)
            
            # 简单的URL验证，实际项目中需要实现加密验证
            # TODO: 实现企业微信加密验证逻辑
            logger.info(f"URL验证成功: {echostr}")
            return echostr
        except Exception as e:
            logger.error(f"URL验证失败: {e}")
            raise

    def parse_message(
        self, body: bytes, msg_signature: str, timestamp: str, nonce: str
    ) -> Dict[str, Any]:
        """解析消息"""
        try:
            # 解析XML
            root = ET.fromstring(body.decode())
            encrypt = root.find("Encrypt")
            
            if encrypt is not None and encrypt.text:
                # 加密消息，需要解密
                # TODO: 实现消息解密逻辑
                logger.info("收到加密消息，解密功能待实现")
                return None
            else:
                # 明文消息，直接解析
                return self._parse_plain_message(body.decode())

        except Exception as e:
            logger.error(f"解析消息失败: {e}")
            raise

    def _parse_plain_message(self, xml_content: str) -> Dict[str, Any]:
        """解析明文消息"""
        try:
            root = ET.fromstring(xml_content)
            
            # 获取基础信息
            msg_type = root.find("MsgType").text if root.find("MsgType") is not None else "unknown"
            from_user = root.find("FromUserName").text if root.find("FromUserName") is not None else ""
            create_time = root.find("CreateTime").text if root.find("CreateTime") is not None else ""
            
            # 处理事件消息
            if msg_type == "event":
                event = root.find("Event").text if root.find("Event") is not None else ""
                return {
                    "msg_type": msg_type,
                    "event": event,
                    "from_user": from_user,
                    "create_time": create_time,
                }

            # 处理文本消息
            elif msg_type == "text":
                content = root.find("Content").text if root.find("Content") is not None else ""
                return {
                    "msg_type": msg_type,
                    "content": content,
                    "from_user": from_user,
                    "create_time": create_time,
                }

            # 处理图片消息
            elif msg_type == "image":
                pic_url = root.find("PicUrl").text if root.find("PicUrl") is not None else ""
                return {
                    "msg_type": msg_type,
                    "pic_url": pic_url,
                    "from_user": from_user,
                    "create_time": create_time,
                }

            # 处理语音消息
            elif msg_type == "voice":
                voice_format = root.find("Format").text if root.find("Format") is not None else "amr"
                return {
                    "msg_type": msg_type,
                    "voice_format": voice_format,
                    "from_user": from_user,
                    "create_time": create_time,
                }

            else:
                logger.info(f"不支持的消息类型: {msg_type}")
                return {
                    "msg_type": msg_type,
                    "from_user": from_user,
                    "create_time": create_time,
                }

        except Exception as e:
            logger.error(f"解析明文消息失败: {e}")
            raise

    def get_access_token(self) -> str:
        """获取访问令牌"""
        current_time = int(time.time())

        # 如果 token 还有效（提前5分钟刷新）
        if self.access_token and self.access_token_expires > current_time + 300:
            return self.access_token

        url = f"{self.api_url}/gettoken?corpid={self.corp_id}&corpsecret={self.secret}"
        try:
            response = httpx.get(url)
            response.raise_for_status()
            result = response.json()
            if result["errcode"] == 0:
                self.access_token = result["access_token"]
                # 记录过期时间戳
                self.access_token_expires = current_time + result["expires_in"]
                return self.access_token
            else:
                raise Exception(f"获取access_token失败: {result}")
        except Exception as e:
            logger.error(f"获取access_token失败: {e}")
            raise

    async def send_text_message(self, user_id: str, content: str) -> None:
        """发送文本消息"""
        try:
            access_token = self.get_access_token()
            url = f"{self.api_url}/message/send?access_token={access_token}"
            data = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {"content": content},
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                result = response.json()
                if result["errcode"] != 0:
                    # 如果是 token 过期，清除 token 并重试一次
                    if result["errcode"] == 42001:
                        self.access_token = None
                        self.access_token_expires = 0
                        return await self.send_text_message(user_id, content)

                    error_msg = f"发送消息失败: {result}"
                    logger.error(error_msg)
                    # 如果是IP白名单问题，给出更友好的提示
                    if result["errcode"] == 60020:
                        raise Exception("服务器IP未添加到企业微信白名单，请联系管理员")
                    raise Exception(error_msg)
                    
                logger.info(f"文本消息发送成功: {user_id}")
                
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            raise

    async def send_markdown_message(self, user_id: str, content: str) -> None:
        """发送markdown消息"""
        try:
            access_token = self.get_access_token()
            url = f"{self.api_url}/message/send?access_token={access_token}"
            data = {
                "touser": user_id,
                "msgtype": "markdown",
                "agentid": self.agent_id,
                "markdown": {"content": content},
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                result = response.json()
                if result["errcode"] != 0:
                    # 如果是 token 过期，清除 token 并重试一次
                    if result["errcode"] == 42001:
                        self.access_token = None
                        self.access_token_expires = 0
                        return await self.send_markdown_message(user_id, content)

                    error_msg = f"发送markdown消息失败: {result}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                    
                logger.info(f"Markdown消息发送成功: {user_id}")
                
        except Exception as e:
            logger.error(f"发送markdown消息失败: {e}")
            raise

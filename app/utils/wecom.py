import json
import logging
import time
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, Dict

import httpx

from ..core.config import get_settings
from .crypto import WeChatCrypto
from .text_to_pdf import text_to_pdf

logger = logging.getLogger(__name__)


class WeComService:
    def __init__(self):
        settings = get_settings()
        self.corp_id = settings.WECOM_CORP_ID
        self.agent_id = settings.WECOM_AGENT_ID
        self.secret = settings.WECOM_AGENT_SECRET
        self.token = settings.WECOM_TOKEN
        self.encoding_aes_key = settings.WECOM_ENCODING_AES_KEY
        self.crypto = WeChatCrypto(self.token, self.encoding_aes_key, self.corp_id)
        self.access_token = None
        self.access_token_expires = 0
        self.api_url = "https://qyapi.weixin.qq.com/cgi-bin"

    def verify_url(
        self, msg_signature: str, timestamp: str, nonce: str, echostr: str
    ) -> str:
        """验证回调URL"""
        try:
            logger.debug(
                f"开始验证URL: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}"
            )
            echostr = urllib.parse.unquote(echostr)
            decrypted = self.crypto.verify_url(msg_signature, timestamp, nonce, echostr)
            logger.info(f"URL验证成功: {decrypted}")
            return decrypted
        except Exception as e:
            logger.error(f"URL验证失败: {e}")
            raise

    def decrypt_message(
        self, encrypt_msg: str, msg_signature: str, timestamp: str, nonce: str
    ) -> str:
        """解密消息"""
        try:
            return self.crypto.decrypt_message(
                encrypt_msg, msg_signature, timestamp, nonce
            )
        except Exception as e:
            logger.error(f"消息解密失败: {e}")
            raise

    def parse_message(
        self, body: bytes, msg_signature: str, timestamp: str, nonce: str
    ) -> Dict[str, Any]:
        """解析消息"""
        try:
            # 解析XML
            root = ET.fromstring(body.decode())
            encrypt = root.find("Encrypt").text

            # 解密消息
            decrypted = self.decrypt_message(encrypt, msg_signature, timestamp, nonce)
            logger.info(f"解密后的消息: {decrypted}")

            # 解析XML
            msg_root = ET.fromstring(decrypted)

            # 获取基础信息，添加安全检查
            msg_type_elem = msg_root.find("MsgType")
            from_user_elem = msg_root.find("FromUserName")
            create_time_elem = msg_root.find("CreateTime")

            if msg_type_elem is None or msg_type_elem.text is None:
                logger.error("消息缺少MsgType字段")
                raise ValueError("消息缺少MsgType字段")

            if from_user_elem is None or from_user_elem.text is None:
                logger.error("消息缺少FromUserName字段")
                raise ValueError("消息缺少FromUserName字段")

            if create_time_elem is None or create_time_elem.text is None:
                logger.error("消息缺少CreateTime字段")
                raise ValueError("消息缺少CreateTime字段")

            msg_type = msg_type_elem.text
            from_user = from_user_elem.text
            create_time = create_time_elem.text

            # 处理事件消息（事件消息没有MsgId）
            if msg_type == "event":
                event = msg_root.find("Event").text
                agent_id = (
                    msg_root.find("AgentID").text
                    if msg_root.find("AgentID") is not None
                    else None
                )

                return {
                    "msg_type": msg_type,
                    "event": event,
                    "from_user": from_user,
                    "create_time": create_time,
                    "agent_id": agent_id,
                }

            # 获取消息ID（非事件消息才有MsgId）
            msg_id_elem = msg_root.find("MsgId")
            msg_id = msg_id_elem.text if msg_id_elem is not None else None

            # 处理文本消息
            if msg_type == "text":
                content = msg_root.find("Content").text
                return {
                    "msg_type": msg_type,
                    "content": content,
                    "from_user": from_user,
                    "msg_id": msg_id,
                    "create_time": create_time,
                }

            # 处理图片消息
            elif msg_type == "image":
                pic_url = (
                    msg_root.find("PicUrl").text
                    if msg_root.find("PicUrl") is not None
                    else None
                )
                media_id = (
                    msg_root.find("MediaId").text
                    if msg_root.find("MediaId") is not None
                    else None
                )
                return {
                    "msg_type": msg_type,
                    "pic_url": pic_url,
                    "media_id": media_id,
                    "from_user": from_user,
                    "msg_id": msg_id,
                    "create_time": create_time,
                }

            # 处理位置消息
            elif msg_type == "location":
                location_x = msg_root.find("Location_X").text  # 纬度
                location_y = msg_root.find("Location_Y").text  # 经度
                scale = msg_root.find("Scale").text  # 地图缩放大小
                label = msg_root.find("Label").text  # 地理位置信息

                return {
                    "msg_type": msg_type,
                    "location": {
                        "latitude": location_x,
                        "longitude": location_y,
                        "scale": scale,
                        "label": label,
                    },
                    "from_user": from_user,
                    "msg_id": msg_id,
                    "create_time": create_time,
                }

            # 处理语音消息
            elif msg_type == "voice":
                # 提取语音文件信息，添加安全检查
                media_id_elem = msg_root.find("MediaId")
                format_elem = msg_root.find("Format")

                if media_id_elem is None or media_id_elem.text is None:
                    logger.error("语音消息缺少MediaId字段")
                    raise ValueError("语音消息缺少MediaId字段")

                if format_elem is None or format_elem.text is None:
                    logger.error("语音消息缺少Format字段")
                    raise ValueError("语音消息缺少Format字段")

                media_id = media_id_elem.text
                voice_format = format_elem.text

                # 获取语音文件URL（需要调用企业微信API）
                voice_url = self._get_media_url(media_id)

                logger.info(f"收到语音消息，格式: {voice_format}, MediaId: {media_id}")
                return {
                    "msg_type": "voice",
                    "voice_url": voice_url,
                    "voice_format": voice_format,
                    "media_id": media_id,
                    "from_user": from_user,
                    "msg_id": msg_id,
                    "create_time": create_time,
                }

            else:
                logger.info(f"不支持的消息类型: {msg_type}")
                return {
                    "msg_type": msg_type,
                    "from_user": from_user,
                    "msg_id": msg_id,
                    "create_time": create_time,
                }
        except Exception as e:
            logger.error(f"解析消息失败: {e}")
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

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """获取用户详细信息"""
        try:
            access_token = self.get_access_token()
            url = (
                f"{self.api_url}/user/get?access_token={access_token}&userid={user_id}"
            )

            response = httpx.get(url)
            response.raise_for_status()
            result = response.json()

            if result["errcode"] == 0:
                logger.info(f"获取用户信息成功: {user_id}")
                return result
            else:
                logger.warning(f"获取用户信息失败: {result}")
                return {"errcode": result["errcode"], "errmsg": result["errmsg"]}

        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return {"errcode": -1, "errmsg": str(e)}

    def _get_media_url(self, media_id: str) -> str:
        """获取媒体文件下载URL"""
        try:
            access_token = self.get_access_token()
            url = f"{self.api_url}/media/get?access_token={access_token}&media_id={media_id}"

            # 返回完整的下载URL
            return url

        except Exception as e:
            logger.error(f"获取媒体文件URL失败: {e}")
            return ""

    async def download_media_file(self, media_id: str, file_path: str) -> bool:
        """
        下载企业微信媒体文件

        Args:
            media_id: 媒体文件ID
            file_path: 保存路径

        Returns:
            是否下载成功
        """
        try:
            import httpx

            # 获取access_token
            access_token = self.get_access_token()

            # 企业微信媒体文件下载API
            download_url = f"{self.api_url}/media/get?access_token={access_token}&media_id={media_id}"

            logger.info(f"开始下载企业微信媒体文件: {media_id}")

            # 下载媒体文件
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(download_url)
                response.raise_for_status()

                # 检查响应内容类型
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    # 如果返回的是JSON错误信息
                    error_data = response.json()
                    if "errcode" in error_data and error_data["errcode"] != 0:
                        logger.error(f"企业微信API错误: {error_data}")
                        return False

                # 写入文件
                with open(file_path, "wb") as f:
                    f.write(response.content)

                logger.info(
                    f"企业微信媒体文件下载成功: {media_id}, 大小: {len(response.content)} bytes"
                )
                return True

        except Exception as e:
            logger.error(f"下载企业微信媒体文件失败: {e}")
            return False

    def get_department_info(self, department_id: int) -> Dict[str, Any]:
        """获取部门详细信息"""
        try:

            access_token = self.get_access_token()
            url = f"{self.api_url}/department/get?access_token={access_token}&id={department_id}"

            response = httpx.get(url)
            response.raise_for_status()
            result = response.json()

            if result["errcode"] == 0:
                logger.info(f"获取部门信息成功: {department_id}")
                # 企业微信API返回的部门信息在department字段中
                department_info = result.get("department", {})
                dept_data = {
                    "errcode": 0,
                    "name": department_info.get("name", f"部门{department_id}"),
                    "id": department_info.get("id", department_id),
                    "parentid": department_info.get("parentid"),
                }

                return dept_data
            else:
                logger.warning(f"获取部门信息失败: {result}")
                return {"errcode": result["errcode"], "errmsg": result["errmsg"]}

        except Exception as e:
            logger.error(f"获取部门信息失败: {e}")
            return {"errcode": -1, "errmsg": str(e)}

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
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            raise

    async def send_markdown_message(self, user_id: str, content: str) -> None:
        """发送markdown消息，支持长消息生成文件"""
        try:
            # 企业微信markdown消息长度限制约为2048字符，留一些余量
            max_length = 1000

            logger.info(f"消息长度: {len(content)} 字符，阈值: {max_length}")

            if len(content) > max_length:
                # 消息过长，生成PDF文件
                logger.info("消息长度超过阈值，生成PDF文件")
                await self._send_pdf_file(user_id, content)
            else:
                # 消息长度在限制内，直接发送
                logger.info("消息长度在阈值内，直接发送markdown消息")
                await self._send_single_markdown_message(user_id, content)

        except Exception as e:
            logger.error(f"发送markdown消息失败: {e}")
            # 如果markdown发送失败，尝试发送文本消息
            try:
                logger.info("尝试发送文本消息作为备选")
                await self.send_text_message(user_id, content)
            except Exception as text_error:
                logger.error(f"文本消息发送也失败: {text_error}")
                raise

    async def _send_single_markdown_message(self, user_id: str, content: str) -> None:
        """发送单条markdown消息"""
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
                        return await self._send_single_markdown_message(
                            user_id, content
                        )

                    error_msg = f"发送markdown消息失败: {result}"
                    logger.error(error_msg)
                    # 如果是IP白名单问题，给出更友好的提示
                    if result["errcode"] == 60020:
                        raise Exception("服务器IP未添加到企业微信白名单，请联系管理员")
                    raise Exception(error_msg)
        except Exception as e:
            logger.error(f"发送单条markdown消息失败: {e}")
            raise

    async def _send_split_markdown_messages(
        self, user_id: str, content: str, max_length: int
    ) -> None:
        """分段发送长markdown消息"""
        try:
            # 按段落分割内容
            paragraphs = content.split("\n\n")
            current_message = ""
            message_count = 0

            for paragraph in paragraphs:
                # 如果当前段落加上当前消息会超长，先发送当前消息
                if (
                    len(current_message) + len(paragraph) + 2 > max_length
                    and current_message
                ):
                    message_count += 1
                    await self._send_single_markdown_message(
                        user_id, current_message.strip()
                    )
                    current_message = paragraph
                else:
                    # 添加段落到当前消息
                    if current_message:
                        current_message += "\n\n" + paragraph
                    else:
                        current_message = paragraph

            # 发送最后一条消息
            if current_message.strip():
                message_count += 1
                await self._send_single_markdown_message(
                    user_id, current_message.strip()
                )

            logger.info(f"长消息已分段发送，共发送 {message_count} 条消息")

        except Exception as e:
            logger.error(f"分段发送markdown消息失败: {e}")
            raise

    async def _send_pdf_file(self, user_id: str, content: str) -> None:
        """生成PDF文件并通过企业微信发送"""
        try:
            import os
            from datetime import datetime

            # 生成PDF文件
            pdf_path = text_to_pdf(content, filename_prefix="wechat_response")

            # 构建文件信息
            file_info = f"""📄 **消息内容过长，正在生成PDF文件...**

**文件信息：**
- 大小：{len(content)} 字符
- 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""

            if pdf_path:
                pdf_filename = os.path.basename(pdf_path)
                file_info += f"""
- PDF文件：{pdf_filename}"""

            file_info += """

💡 PDF版本更适合预览和分享"""

            await self._send_single_markdown_message(user_id, file_info)

            if pdf_path:
                # 上传PDF文件到企业微信
                media_id = await self._upload_file(pdf_path, pdf_filename)

                # 发送文件消息
                await self._send_file_message(user_id, media_id, pdf_filename)

                logger.info(f"已生成并发送PDF文件: {pdf_path}")
            else:
                logger.warning("PDF文件生成失败，无法发送文件")

        except Exception as e:
            logger.error(f"生成PDF文件失败: {e}")
            # 如果生成PDF失败，回退到分段发送
            await self._send_split_markdown_messages(user_id, content, 1800)

    async def _upload_file(self, file_path: str, filename: str) -> str:
        """上传PDF文件到企业微信，返回media_id"""
        try:
            access_token = self.get_access_token()
            url = f"{self.api_url}/media/upload?access_token={access_token}&type=file"

            # 根据文件扩展名确定MIME类型
            if filename.endswith(".pdf"):
                mime_type = "application/pdf"
            elif filename.endswith(".md"):
                mime_type = "text/markdown"
            else:
                mime_type = "application/octet-stream"

            # 读取文件内容
            with open(file_path, "rb") as f:
                files = {"media": (filename, f, mime_type)}

                async with httpx.AsyncClient() as client:
                    response = await client.post(url, files=files)
                    response.raise_for_status()
                    result = response.json()

                    if result["errcode"] == 0:
                        media_id = result["media_id"]
                        logger.info(f"文件上传成功: {filename}, media_id: {media_id}")
                        return media_id
                    else:
                        raise Exception(f"文件上传失败: {result}")

        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise

    async def _send_file_message(
        self, user_id: str, media_id: str, filename: str
    ) -> None:
        """发送文件消息"""
        try:
            access_token = self.get_access_token()
            url = f"{self.api_url}/message/send?access_token={access_token}"
            data = {
                "touser": user_id,
                "msgtype": "file",
                "agentid": self.agent_id,
                "file": {"media_id": media_id},
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                result = response.json()

                if result["errcode"] == 0:
                    logger.info(f"文件消息发送成功: {filename}")
                else:
                    raise Exception(f"文件消息发送失败: {result}")

        except Exception as e:
            logger.error(f"文件消息发送失败: {e}")
            raise

    async def send_location_message(
        self,
        user_id: str,
        latitude: str,
        longitude: str,
        title: str,
        address: str,
        scale: int = 15,
    ) -> None:
        """发送位置消息

        Args:
            user_id: 用户ID
            latitude: 纬度
            longitude: 经度
            title: 位置名称
            address: 地址详情
            scale: 地图缩放级别，默认15
        """
        try:
            access_token = self.get_access_token()
            url = f"{self.api_url}/message/send?access_token={access_token}"
            data = {
                "touser": user_id,
                "msgtype": "location",
                "agentid": self.agent_id,
                "location": {
                    "latitude": str(latitude),  # 确保是字符串格式
                    "longitude": str(longitude),  # 确保是字符串格式
                    "title": title,
                    "address": address,
                    "scale": scale,
                },
            }

            logger.debug(f"发送位置消息数据: {data}")

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                result = response.json()
                if result["errcode"] != 0:
                    # 如果是 token 过期，清除 token 并重试一次
                    if result["errcode"] == 42001:
                        self.access_token = None
                        self.access_token_expires = 0
                        return await self.send_location_message(
                            user_id, latitude, longitude, title, address, scale
                        )

                    error_msg = f"发送位置消息失败: {result}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                logger.info(f"位置消息发送成功: {title}")
        except Exception as e:
            logger.error(f"发送位置消息失败: {e}")
            raise

    def download_media(self, media_id: str) -> bytes:
        """下载媒体文件（暂时禁用）"""
        raise NotImplementedError("媒体文件下载功能暂未实现")

    def recognize_speech(self, audio_data: bytes, format_type: str = "amr") -> str:
        """语音识别（暂时禁用）"""
        return "[语音识别功能暂未实现]"

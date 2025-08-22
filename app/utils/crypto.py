import base64
import hashlib
import logging
import random
import string
import struct
import time

from Crypto.Cipher import AES

logger = logging.getLogger(__name__)


class WeChatCrypto:
    def __init__(self, token: str, encoding_aes_key: str, corp_id: str):
        self.token = token
        self.corp_id = corp_id

        # 处理 encoding_aes_key
        if len(encoding_aes_key) != 43:
            raise ValueError("encoding_aes_key 长度必须为43位")

        # 添加 padding
        key = encoding_aes_key + "="
        try:
            self.key = base64.b64decode(key)
            if len(self.key) != 32:
                raise ValueError("encoding_aes_key 解码后长度必须为32字节")
        except Exception as e:
            logger.error(f"encoding_aes_key 解码失败: {e}")
            raise ValueError(f"encoding_aes_key 格式错误: {e}")

    def verify_url(
        self, msg_signature: str, timestamp: str, nonce: str, echostr: str
    ) -> str:
        """验证回调URL"""
        try:
            # 验证签名
            signature = self._get_signature(timestamp, nonce, echostr)
            if signature != msg_signature:
                logger.error(f"签名不匹配: 计算值={signature}, 接收值={msg_signature}")
                raise ValueError("签名验证失败")

            # 解密
            cipher = AES.new(self.key, AES.MODE_CBC, self.key[:16])
            decrypted = cipher.decrypt(base64.b64decode(echostr))

            # 去除补位字符
            def unpad(s):
                return s[: -ord(s[len(s) - 1 :])]

            decrypted = unpad(decrypted)

            # 去除16位随机字符串
            content = decrypted[16:]
            xml_len = struct.unpack("!I", content[:4])[0]
            xml_content = content[4 : xml_len + 4]
            from_corp_id = content[xml_len + 4 :]

            # 验证corp_id
            if from_corp_id.decode() != self.corp_id:
                logger.error(
                    f"corp_id不匹配: 解密值={from_corp_id.decode()}, 配置值={self.corp_id}"
                )
                raise ValueError("corp_id验证失败")

            return xml_content.decode()
        except Exception as e:
            logger.error(f"URL验证失败: {e}")
            raise ValueError(f"解密失败: {e}")

    def decrypt_message(
        self, encrypt_msg: str, msg_signature: str, timestamp: str, nonce: str
    ) -> str:
        """解密消息"""
        try:
            # 验证签名
            signature = self._get_signature(timestamp, nonce, encrypt_msg)
            if signature != msg_signature:
                logger.error(f"签名不匹配: 计算值={signature}, 接收值={msg_signature}")
                raise ValueError("签名验证失败")

            # 解密
            cipher = AES.new(self.key, AES.MODE_CBC, self.key[:16])
            decrypted = cipher.decrypt(base64.b64decode(encrypt_msg))

            # 去除补位字符
            def unpad(s):
                return s[: -ord(s[len(s) - 1 :])]

            decrypted = unpad(decrypted)

            # 去除16位随机字符串
            content = decrypted[16:]
            xml_len = struct.unpack("!I", content[:4])[0]
            xml_content = content[4 : xml_len + 4]
            from_corp_id = content[xml_len + 4 :]

            # 验证corp_id
            if from_corp_id.decode() != self.corp_id:
                logger.error(
                    f"corp_id不匹配: 解密值={from_corp_id.decode()}, 配置值={self.corp_id}"
                )
                raise ValueError("corp_id验证失败")

            return xml_content.decode()
        except Exception as e:
            logger.error(f"消息解密失败: {e}")
            raise ValueError(f"解密失败: {e}")

    def encrypt_message(self, msg: str, timestamp: str, nonce: str) -> tuple:
        """加密消息"""
        try:
            # 生成16位随机字符串
            random_str = "".join(
                random.choices(string.ascii_letters + string.digits, k=16)
            )

            # 拼接字符串
            text = (
                random_str.encode()
                + struct.pack("!I", len(msg.encode()))
                + msg.encode()
                + self.corp_id.encode()
            )

            # 补位
            def pad(s):
                return s + (32 - len(s) % 32) * chr(32 - len(s) % 32).encode()

            text = pad(text)

            # 加密
            cipher = AES.new(self.key, AES.MODE_CBC, self.key[:16])
            encrypted = cipher.encrypt(text)

            # 生成签名
            encrypt_msg = base64.b64encode(encrypted).decode()
            signature = self._get_signature(timestamp, nonce, encrypt_msg)

            return encrypt_msg, signature
        except Exception as e:
            logger.error(f"消息加密失败: {e}")
            raise

    def _get_signature(self, timestamp: str, nonce: str, encrypt_msg: str) -> str:
        """生成签名"""
        # 按字典序排序
        arr = [self.token, timestamp, nonce, encrypt_msg]
        arr.sort()
        # 拼接字符串
        str_to_sign = "".join(arr)
        # SHA1 加密
        return hashlib.sha1(str_to_sign.encode()).hexdigest()

    def create_response_package(self, reply_msg: str) -> str:
        """构造被动响应包"""
        try:
            # 生成时间戳和随机数
            timestamp = str(int(time.time()))
            nonce = "".join(random.choices(string.ascii_letters + string.digits, k=16))

            # 加密消息
            encrypt_msg, signature = self.encrypt_message(reply_msg, timestamp, nonce)

            # 构造响应包
            response = f"""<xml>
<Encrypt><![CDATA[{encrypt_msg}]]></Encrypt>
<MsgSignature><![CDATA[{signature}]]></MsgSignature>
<TimeStamp>{timestamp}</TimeStamp>
<Nonce><![CDATA[{nonce}]]></Nonce>
</xml>"""
            return response
        except Exception as e:
            logger.error(f"构造响应包失败: {e}")
            raise

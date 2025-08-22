from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "企业微信消息接收服务"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = ""

    # 基础配置
    DEBUG: str = "false"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: str = "logs"
    LOG_FILE: str = "app.log"

    # Redis配置（可选，用于缓存企业微信用户信息）
    USE_REDIS_CACHE: str = "false"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # 企业微信配置
    WECOM_CORP_ID: Optional[str] = None
    WECOM_AGENT_ID: Optional[str] = None
    WECOM_AGENT_SECRET: Optional[str] = None
    WECOM_TOKEN: Optional[str] = None
    WECOM_ENCODING_AES_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="allow"
    )


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    settings = Settings()

    # 手动解析布尔值
    def parse_bool(value: str) -> bool:
        if isinstance(value, str):
            return value.lower().strip().split("#")[0].strip() in ("true", "1", "t", "yes", "y")
        return bool(value)

    # 转换为布尔值
    settings.DEBUG = parse_bool(settings.DEBUG)
    settings.USE_REDIS_CACHE = parse_bool(settings.USE_REDIS_CACHE)

    return settings


# 创建全局配置实例
settings = get_settings()

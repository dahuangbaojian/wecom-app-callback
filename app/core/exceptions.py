"""
自定义异常类定义
"""


class AIAssistantException(Exception):
    """智能助手基础异常类"""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ConfigurationError(AIAssistantException):
    """配置错误"""

    pass


class CacheError(AIAssistantException):
    """缓存错误"""

    pass


class ValidationError(AIAssistantException):
    """数据验证错误"""

    pass


class NetworkError(AIAssistantException):
    """网络请求错误"""

    pass


class TimeoutError(AIAssistantException):
    """超时错误"""

    pass


class RateLimitError(AIAssistantException):
    """频率限制错误"""

    pass


class AuthenticationError(AIAssistantException):
    """认证错误"""

    pass


class AuthorizationError(AIAssistantException):
    """授权错误"""

    pass


class ResourceNotFoundError(AIAssistantException):
    """资源未找到错误"""

    pass


class ServiceUnavailableError(AIAssistantException):
    """服务不可用错误"""

    pass


class DataFormatError(AIAssistantException):
    """数据格式错误"""

    pass


class BusinessLogicError(AIAssistantException):
    """业务逻辑错误"""

    pass

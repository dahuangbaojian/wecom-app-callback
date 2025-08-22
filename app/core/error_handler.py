"""
全局异常处理器
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorHandler:
    """全局异常处理器"""

    @staticmethod
    def handle_exception(e: Exception, context: str = "", user_id: str = None) -> Dict[str, Any]:
        """
        统一异常处理

        Args:
            e: 异常对象
            context: 异常上下文
            user_id: 用户ID

        Returns:
            错误响应字典 {code, message}
        """
        # 记录异常详情
        logger.error(
            f"异常处理 - 上下文: {context}, 用户: {user_id}, 异常: {str(e)}",
            extra={"user_id": user_id, "context": context},
            exc_info=True,
        )

        # 根据异常类型返回不同的错误信息
        if isinstance(e, ValueError):
            return {
                "code": 400,
                "message": f"参数错误: {str(e)}",
            }

        if isinstance(e, KeyError):
            return {
                "code": 400,
                "message": f"缺少必要参数: {str(e)}",
            }

        # 默认错误处理
        return {
            "code": 500,
            "message": "系统内部错误，请联系管理员",
        }


def error_handler(context: str = ""):
    """
    异常处理装饰器

    Args:
        context: 异常上下文描述
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # 提取用户ID
                user_id = kwargs.get("user_id", "unknown")
                error_result = ErrorHandler.handle_exception(e, context, user_id)

                # 直接返回错误信息字符串
                error_message = error_result["message"]
                if isinstance(error_message, dict):
                    error_message = str(error_message)
                return error_message

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 提取用户ID
                user_id = kwargs.get("user_id", "unknown")
                error_result = ErrorHandler.handle_exception(e, context, user_id)

                # 直接返回错误信息字符串
                error_message = error_result["message"]
                if isinstance(error_message, dict):
                    error_message = str(error_message)
                return error_message

        # 根据函数类型返回对应的包装器
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    FastAPI全局异常处理器
    """
    # 提取用户ID
    user_id = request.headers.get("x-user-id", "unknown")

    # 处理异常
    error_response = ErrorHandler.handle_exception(exc, "HTTP请求处理", user_id)

    # 返回JSON响应
    return JSONResponse(
        content={
            "code": error_response["code"],
            "message": error_response["message"],
        },
    )

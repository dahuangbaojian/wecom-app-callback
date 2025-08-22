import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

# 全局变量，用于跟踪日志是否已初始化
_logging_initialized = False
_logging_log_name = None


class UserIDFilter(logging.Filter):
    """为日志记录添加用户ID字段的过滤器"""

    def filter(self, record):
        record.user_id = getattr(record, "user_id", "system")
        return True


def setup_logging(log_name="app"):
    """
    通用日志系统初始化
    log_name: 日志文件前缀，默认为"app"，生成 logs/app.log 和 logs/app_error.log
    如果指定其他名称，则生成 logs/{log_name}.log 和 logs/{log_name}_error.log
    日志格式统一，带user_id字段，按天备份
    """
    global _logging_initialized, _logging_log_name

    # 延迟导入，避免循环导入问题
    from ai_smart_assistant.core.config import get_settings

    settings = get_settings()

    # 创建日志目录
    if not os.path.exists(settings.LOG_DIR):
        os.makedirs(settings.LOG_DIR)

    # 配置root logger，这样所有getLogger(__name__)都能输出
    # 只在第一次调用时配置root logger
    if not _logging_initialized:
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(user_id)s] - %(message)s"
        )

        # 控制台输出
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(UserIDFilter())
        console_handler.setLevel(settings.LOG_LEVEL)
        root_logger.addHandler(console_handler)

        # 主日志文件
        main_log_file = os.path.join(settings.LOG_DIR, f"{log_name}.log")
        main_file_handler = TimedRotatingFileHandler(
            main_log_file,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
            delay=False,
        )
        main_file_handler.suffix = "%Y-%m-%d"
        main_file_handler.setFormatter(formatter)
        main_file_handler.addFilter(UserIDFilter())
        main_file_handler.setLevel(settings.LOG_LEVEL)
        root_logger.addHandler(main_file_handler)

        # 错误日志文件
        error_log_file = os.path.join(settings.LOG_DIR, f"{log_name}_error.log")
        error_file_handler = TimedRotatingFileHandler(
            error_log_file,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
            delay=False,
        )
        error_file_handler.suffix = "%Y-%m-%d"
        error_file_handler.setFormatter(formatter)
        error_file_handler.addFilter(UserIDFilter())
        error_file_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_file_handler)

        # 标记日志已初始化
        _logging_initialized = True
        _logging_log_name = log_name

        # 使用root logger记录初始化信息
        root_logger.info(
            f"日志系统初始化完成，主日志文件: logs/{log_name}.log，错误日志文件: logs/{log_name}_error.log"
        )
        root_logger.info("日志配置: 按日期归档，保留30天，追加模式")

    # 为特定模块创建独立的日志文件（如果log_name不是"app"）
    if log_name != "app":
        # 创建该模块的独立logger
        module_logger = logging.getLogger(log_name)

        # 如果这个logger已经配置过，直接返回
        if module_logger.handlers:
            return module_logger

        module_logger.setLevel(settings.LOG_LEVEL)
        module_logger.propagate = False  # 不向上传播，避免重复输出

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(user_id)s] - %(message)s"
        )

        # 模块专用日志文件
        module_log_file = os.path.join(settings.LOG_DIR, f"{log_name}.log")
        module_file_handler = TimedRotatingFileHandler(
            module_log_file,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
            delay=False,
        )
        module_file_handler.suffix = "%Y-%m-%d"
        module_file_handler.setFormatter(formatter)
        module_file_handler.addFilter(UserIDFilter())
        module_file_handler.setLevel(settings.LOG_LEVEL)
        module_logger.addHandler(module_file_handler)

        # 模块专用错误日志文件
        module_error_log_file = os.path.join(settings.LOG_DIR, f"{log_name}_error.log")
        module_error_file_handler = TimedRotatingFileHandler(
            module_error_log_file,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
            delay=False,
        )
        module_error_file_handler.suffix = "%Y-%m-%d"
        module_error_file_handler.setFormatter(formatter)
        module_error_file_handler.addFilter(UserIDFilter())
        module_error_file_handler.setLevel(logging.ERROR)
        module_logger.addHandler(module_error_file_handler)

        module_logger.info(
            f"模块日志系统初始化完成，日志文件: {module_log_file}，错误日志文件: {module_error_log_file}"
        )
        return module_logger

    # 返回root logger，所有模块都使用这个
    return logging.getLogger()

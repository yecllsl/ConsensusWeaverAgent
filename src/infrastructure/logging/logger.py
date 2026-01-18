import logging
import logging.handlers
import os
from typing import Any, Optional


class Logger:
    def __init__(
        self,
        name: str = "ConsensusWeaver",
        log_file: str = "consensusweaver.log",
        log_level: str = "info",
    ):
        self.name = name
        self.log_file = log_file
        self.log_level = self._get_log_level(log_level)
        self.logger = self._setup_logger()

    def _get_log_level(self, log_level: str) -> int:
        """将字符串日志级别转换为logging模块的整数级别"""
        log_level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        return log_level_map.get(log_level.lower(), logging.INFO)

    def _setup_logger(self) -> logging.Logger:
        """配置日志记录器"""

        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        logger.propagate = False

        # 清除已有的处理器
        if logger.handlers:
            logger.handlers.clear()

        # 创建格式器
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 确保日志文件目录存在
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 创建文件处理器（带轮转）
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,  # 保存5个备份
            encoding="utf-8",
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录调试信息"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录一般信息"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录警告信息"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录错误信息"""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录严重错误信息"""
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录异常信息"""
        self.logger.exception(message, *args, **kwargs)

    def set_level(self, log_level: str) -> None:
        """设置日志级别"""
        self.log_level = self._get_log_level(log_level)
        self.logger.setLevel(self.log_level)
        for handler in self.logger.handlers:
            handler.setLevel(self.log_level)

    def set_log_file(self, log_file: str) -> None:
        """设置日志文件"""
        self.log_file = log_file
        self.logger = self._setup_logger()


# 创建全局日志记录器实例
_global_logger: Optional[Logger] = None


def get_logger(
    name: Optional[str] = None,
    log_file: Optional[str] = None,
    log_level: Optional[str] = None,
) -> Logger:
    """获取日志记录器实例"""
    global _global_logger

    # 如果提供了参数，创建新的日志记录器实例
    if name or log_file or log_level:
        return Logger(
            name=name or "ConsensusWeaver",
            log_file=log_file or "consensusweaver.log",
            log_level=log_level or "info",
        )

    # 否则返回全局单例实例
    if _global_logger is None:
        _global_logger = Logger()
    return _global_logger

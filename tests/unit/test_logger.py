"""日志工具单元测试"""
import logging
from utils.logger import get_logger


def test_get_logger_returns_logger():
    """测试 get_logger 返回 Logger 实例"""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)


def test_get_logger_same_name_returns_same_instance():
    """测试相同名称返回同一个 Logger 实例"""
    logger1 = get_logger("test_module")
    logger2 = get_logger("test_module")
    assert logger1 is logger2


def test_logger_has_handler():
    """测试 logger 至少有一个 handler"""
    logger = get_logger("test_handler_check")
    assert len(logger.handlers) >= 1

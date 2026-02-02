import os

import pytest

from src.infrastructure.logging.logger import get_logger


# 测试日志记录功能
def test_logger_basic(tmp_path):
    log_file = tmp_path / "test.log"
    logger = get_logger(log_file=str(log_file), log_level="info")

    # 记录不同级别的日志
    logger.debug("这是一个debug日志")  # 应该不被记录，因为日志级别是info
    logger.info("这是一个info日志")
    logger.warning("这是一个warning日志")
    logger.error("这是一个error日志")
    logger.critical("这是一个critical日志")

    # 验证日志文件存在
    assert os.path.exists(log_file)

    # 读取日志文件内容
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()

    # 验证日志内容
    assert "这是一个info日志" in log_content
    assert "这是一个warning日志" in log_content
    assert "这是一个error日志" in log_content
    assert "这是一个critical日志" in log_content
    assert "这是一个debug日志" not in log_content  # debug日志不应该被记录


# 测试日志级别设置
def test_logger_level(tmp_path):
    log_file = tmp_path / "test_level.log"

    # 设置debug级别
    logger = get_logger(log_file=str(log_file), log_level="debug")
    logger.debug("这是一个debug日志")

    # 读取日志内容
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()

    # 验证debug日志被记录
    assert "这是一个debug日志" in log_content

    # 修改日志级别为warning
    logger.set_level("warning")
    logger.info("这是一个info日志")  # 应该不被记录
    logger.warning("这是一个warning日志")

    # 读取更新后的日志内容
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()

    # 验证日志级别已更新
    assert "这是一个info日志" not in log_content  # info日志不应该被记录
    assert "这是一个warning日志" in log_content


# 测试异常日志记录
def test_logger_exception(tmp_path):
    log_file = tmp_path / "test_exception.log"
    logger = get_logger(log_file=str(log_file), log_level="error")

    try:
        raise ValueError("测试异常")
    except Exception:
        logger.exception("发生异常")

    # 读取日志内容
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()

    # 验证异常信息被记录
    assert "发生异常" in log_content
    assert "ValueError" in log_content
    assert "测试异常" in log_content
    assert "Traceback" in log_content  # 应该包含堆栈跟踪


# 测试日志文件切换
@pytest.mark.unit
def test_logger_file_switch(tmp_path):
    log_file1 = tmp_path / "test_file1.log"
    log_file2 = tmp_path / "test_file2.log"

    # 使用第一个日志文件
    logger = get_logger(log_file=str(log_file1), log_level="info")
    logger.info("记录到第一个文件")

    # 切换到第二个日志文件
    logger.set_log_file(str(log_file2))
    logger.info("记录到第二个文件")

    # 验证日志文件内容
    with open(log_file1, "r", encoding="utf-8") as f:
        content1 = f.read()

    with open(log_file2, "r", encoding="utf-8") as f:
        content2 = f.read()

    assert "记录到第一个文件" in content1
    assert "记录到第一个文件" not in content2
    assert "记录到第二个文件" in content2
    assert "记录到第二个文件" not in content1

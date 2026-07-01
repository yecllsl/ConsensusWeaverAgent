"""测试级 pytest 配置与 fixtures"""
import pytest
import tempfile
import os
from pathlib import Path

from core.config import Config, BrowserConfig, PlatformConfig, DefaultsConfig, PathsConfig


@pytest.fixture
def test_config():
    """测试用配置 fixture，使用独立的数据目录"""
    tmp_dir = tempfile.mkdtemp(prefix="consensus_test_")
    user_data_dir = os.path.join(tmp_dir, "user_data")
    screenshot_dir = os.path.join(tmp_dir, "screenshots")
    log_dir = os.path.join(tmp_dir, "logs")

    for d in [user_data_dir, screenshot_dir, log_dir]:
        Path(d).mkdir(parents=True, exist_ok=True)

    config = Config(
        browser=BrowserConfig(
            headless=True,
            viewport_width=1280,
            viewport_height=800,
            slow_mo=0,
            user_data_base_dir=user_data_dir,
        ),
        platforms={
            "doubao": PlatformConfig(enabled=True, name="豆包", base_url="https://www.doubao.com"),
            "chatglm": PlatformConfig(enabled=True, name="智谱清言", base_url="https://chatglm.cn"),
            "deepseek": PlatformConfig(enabled=True, name="DeepSeek", base_url="https://chat.deepseek.com"),
            "qianwen": PlatformConfig(enabled=True, name="千问", base_url="https://qianwen.com/chat"),
            "yuanbao": PlatformConfig(enabled=True, name="元宝", base_url="https://yuanbao.tencent.com/chat"),
        },
        defaults=DefaultsConfig(timeout=10, min_success=3, max_concurrent=5),
        paths=PathsConfig(screenshot_dir=screenshot_dir, log_dir=log_dir),
    )
    yield config

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def test_config_partial():
    """部分平台的测试配置（仅 2 个平台）"""
    tmp_dir = tempfile.mkdtemp(prefix="consensus_test_")
    config = Config(
        browser=BrowserConfig(
            headless=True,
            viewport_width=1280,
            viewport_height=800,
            slow_mo=0,
            user_data_base_dir=os.path.join(tmp_dir, "user_data"),
        ),
        platforms={
            "doubao": PlatformConfig(enabled=True, name="豆包", base_url="https://www.doubao.com"),
            "chatglm": PlatformConfig(enabled=True, name="智谱清言", base_url="https://chatglm.cn"),
        },
        defaults=DefaultsConfig(timeout=10, min_success=1, max_concurrent=2),
        paths=PathsConfig(
            screenshot_dir=os.path.join(tmp_dir, "screenshots"),
            log_dir=os.path.join(tmp_dir, "logs"),
        ),
    )
    yield config

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

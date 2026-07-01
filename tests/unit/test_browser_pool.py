"""浏览器池单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.browser_pool import BrowserPool
from core.config import BrowserConfig


@pytest.fixture
def browser_config():
    """浏览器配置 fixture"""
    return BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800,
        slow_mo=0,
        user_data_base_dir="./data/user_data",
    )


def test_browser_pool_init(browser_config):
    """测试浏览器池初始化"""
    pool = BrowserPool(browser_config)
    assert pool.config == browser_config
    assert pool._playwright is None
    assert pool._contexts == {}


def test_browser_pool_user_data_path(browser_config):
    """测试用户数据目录路径生成"""
    pool = BrowserPool(browser_config)
    path = pool._get_user_data_path("doubao")
    assert "doubao" in path
    assert "user_data" in path

"""平台管理器单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.platform_manager import PlatformManager
from core.config import Config, BrowserConfig, PlatformConfig, DefaultsConfig, PathsConfig
from adapters.base_adapter import AdapterResult


@pytest.fixture
def test_config():
    """测试配置"""
    return Config(
        browser=BrowserConfig(headless=True, viewport_width=1280, viewport_height=800, slow_mo=0, user_data_base_dir="./data/user_data"),
        platforms={
            "doubao": PlatformConfig(enabled=True, name="豆包", base_url="https://www.doubao.com"),
            "chatglm": PlatformConfig(enabled=True, name="智谱清言", base_url="https://chatglm.cn"),
        },
        defaults=DefaultsConfig(timeout=120, min_success=3, max_concurrent=5),
        paths=PathsConfig(screenshot_dir="./data/screenshots", log_dir="./data/logs"),
    )


def test_platform_manager_init(test_config):
    """测试平台管理器初始化"""
    mgr = PlatformManager(test_config)
    assert mgr.config == test_config
    assert len(mgr._adapter_registry) == 5  # 注册了 5 个适配器类


def test_platform_manager_get_enabled_platforms(test_config):
    """测试获取已启用平台"""
    mgr = PlatformManager(test_config)
    enabled = mgr.get_enabled_platforms()
    assert "doubao" in enabled
    assert "chatglm" in enabled


@pytest.mark.asyncio
async def test_platform_manager_ask_single_platform(test_config):
    """测试单平台提问（使用 mock）"""
    mgr = PlatformManager(test_config)

    mock_result = AdapterResult(
        platform="doubao",
        platform_name="豆包",
        status="success",
        answer="测试答案",
        duration_ms=1000,
        screenshot_path=None,
        error=None,
    )

    mock_adapter = AsyncMock()
    mock_adapter.ask = AsyncMock(return_value=mock_result)
    mock_adapter.platform_id = "doubao"
    mock_adapter.platform_name = "豆包"

    mgr._create_adapter = AsyncMock(return_value=mock_adapter)
    mgr._browser_pool = AsyncMock()
    mgr._browser_pool.get_page = AsyncMock(return_value=AsyncMock())

    result = await mgr.ask_question("测试问题", ["doubao"], timeout=10, min_success=1)

    assert result["success"] is True
    assert result["success_count"] == 1
    assert result["total_count"] == 1
    assert len(result["results"]) == 1


@pytest.mark.asyncio
async def test_platform_manager_min_success_logic(test_config):
    """测试 min_success 逻辑"""
    mgr = PlatformManager(test_config)

    mock_result_fail = AdapterResult(
        platform="doubao",
        platform_name="豆包",
        status="failed",
        answer=None,
        duration_ms=5000,
        screenshot_path=None,
        error="超时",
    )

    mock_adapter = AsyncMock()
    mock_adapter.ask = AsyncMock(return_value=mock_result_fail)

    mgr._create_adapter = AsyncMock(return_value=mock_adapter)
    mgr._browser_pool = AsyncMock()
    mgr._browser_pool.get_page = AsyncMock(return_value=AsyncMock())

    result = await mgr.ask_question("测试问题", ["doubao", "chatglm"], timeout=10, min_success=1)

    assert result["success"] is False  # 0 成功 < 1 最小要求
    assert result["success_count"] == 0

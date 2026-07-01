"""平台管理器集成测试 - 使用 mock 适配器验证调度逻辑"""
import pytest
from unittest.mock import AsyncMock, patch

from core.platform_manager import PlatformManager
from adapters.base_adapter import AdapterResult


@pytest.mark.integration
@pytest.mark.asyncio
async def test_platform_manager_list_platforms(test_config):
    """测试列出平台"""
    mgr = PlatformManager(test_config)
    result = await mgr.list_platforms()

    assert "platforms" in result
    assert len(result["platforms"]) == 5
    ids = [p["id"] for p in result["platforms"]]
    assert "doubao" in ids
    assert "chatglm" in ids
    assert "deepseek" in ids
    assert "qianwen" in ids
    assert "yuanbao" in ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_platform_manager_ask_with_mock_adapters(test_config_partial):
    """测试并行提问（mock 适配器）"""
    mgr = PlatformManager(test_config_partial)

    mock_result = AdapterResult(
        platform="doubao", platform_name="豆包",
        status="success", answer="豆包的回答",
        duration_ms=1000, screenshot_path=None, error=None,
    )
    mock_result2 = AdapterResult(
        platform="chatglm", platform_name="智谱清言",
        status="success", answer="智谱清言的回答",
        duration_ms=2000, screenshot_path=None, error=None,
    )

    mock_adapter1 = AsyncMock()
    mock_adapter1.ask = AsyncMock(return_value=mock_result)
    mock_adapter2 = AsyncMock()
    mock_adapter2.ask = AsyncMock(return_value=mock_result2)

    mgr._create_adapter = AsyncMock(side_effect=[mock_adapter1, mock_adapter2])

    result = await mgr.ask_question("测试问题", ["doubao", "chatglm"], timeout=10, min_success=1)

    assert result["success"] is True
    assert result["success_count"] == 2
    assert result["total_count"] == 2
    assert len(result["results"]) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_platform_manager_partial_failure(test_config_partial):
    """测试部分平台失败的场景"""
    mgr = PlatformManager(test_config_partial)

    success_result = AdapterResult(
        platform="doubao", platform_name="豆包",
        status="success", answer="回答", duration_ms=1000,
        screenshot_path=None, error=None,
    )
    fail_result = AdapterResult(
        platform="chatglm", platform_name="智谱清言",
        status="failed", answer=None, duration_ms=5000,
        screenshot_path=None, error="超时",
    )

    mock_adapter1 = AsyncMock()
    mock_adapter1.ask = AsyncMock(return_value=success_result)
    mock_adapter2 = AsyncMock()
    mock_adapter2.ask = AsyncMock(return_value=fail_result)

    mgr._create_adapter = AsyncMock(side_effect=[mock_adapter1, mock_adapter2])

    result = await mgr.ask_question("测试问题", ["doubao", "chatglm"], timeout=10, min_success=2)

    assert result["success"] is False
    assert result["success_count"] == 1
    assert result["results"][0]["status"] == "success"
    assert result["results"][1]["status"] == "failed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_platform_manager_all_failed(test_config_partial):
    """测试全部平台失败"""
    mgr = PlatformManager(test_config_partial)

    fail_result = AdapterResult(
        platform="doubao", platform_name="豆包",
        status="failed", answer=None, duration_ms=5000,
        screenshot_path=None, error="连接失败",
    )
    fail_result2 = AdapterResult(
        platform="chatglm", platform_name="智谱清言",
        status="failed", answer=None, duration_ms=5000,
        screenshot_path=None, error="连接失败",
    )

    mock_adapter1 = AsyncMock()
    mock_adapter1.ask = AsyncMock(return_value=fail_result)
    mock_adapter2 = AsyncMock()
    mock_adapter2.ask = AsyncMock(return_value=fail_result2)

    mgr._create_adapter = AsyncMock(side_effect=[mock_adapter1, mock_adapter2])

    result = await mgr.ask_question("测试问题", ["doubao", "chatglm"], timeout=10, min_success=1)

    assert result["success"] is False
    assert result["success_count"] == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_platform_manager_invalid_platform_filtered(test_config):
    """测试不存在的平台被过滤"""
    mgr = PlatformManager(test_config)

    result = await mgr.ask_question(
        "测试问题",
        ["doubao", "nonexistent"],
        timeout=5,
        min_success=1,
    )

    assert result["total_count"] == 1  # 只有 doubao

"""MCP 工具 E2E 测试 - 完整调用链验证"""
import pytest
from unittest.mock import AsyncMock, patch

from adapters.base_adapter import AdapterResult


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_platforms_tool():
    """测试 list_platforms 工具完整调用"""
    from mcp_server import list_platforms

    result = await list_platforms.fn()

    assert "platforms" in result
    assert len(result["platforms"]) == 5
    for p in result["platforms"]:
        assert "id" in p
        assert "name" in p
        assert "url" in p
        assert "enabled" in p


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ask_ai_empty_question():
    """测试 ask_ai 空问题参数校验"""
    from mcp_server import ask_ai

    result = await ask_ai.fn(question="", platforms=["doubao"])
    assert result["success"] is False
    assert "空" in result["error"]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ask_ai_invalid_timeout():
    """测试 ask_ai 非法超时参数"""
    from mcp_server import ask_ai

    result = await ask_ai.fn(question="测试", timeout=0)
    assert result["success"] is False
    assert "超时" in result["error"]

    result2 = await ask_ai.fn(question="测试", timeout=999)
    assert result2["success"] is False


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ask_ai_invalid_min_success():
    """测试 ask_ai 非法 min_success 参数"""
    from mcp_server import ask_ai

    result = await ask_ai.fn(question="测试", min_success=0)
    assert result["success"] is False


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ask_ai_with_mock_manager():
    """测试 ask_ai 工具调用（mock 平台管理器）"""
    from mcp_server import ask_ai, get_manager

    mock_manager = AsyncMock()
    mock_manager.ask_question = AsyncMock(return_value={
        "success": True,
        "total_count": 1,
        "success_count": 1,
        "question": "测试问题",
        "results": [
            {
                "platform": "doubao",
                "platform_name": "豆包",
                "status": "success",
                "answer": "回答",
                "duration_ms": 1000,
                "screenshot_path": None,
                "error": None,
            }
        ],
    })

    with patch("mcp_server.get_manager", return_value=mock_manager):
        result = await ask_ai.fn(question="测试问题", platforms=["doubao"])

    assert result["success"] is True
    assert result["success_count"] == 1
    assert len(result["results"]) == 1
    assert result["results"][0]["platform"] == "doubao"
    assert result["results"][0]["answer"] == "回答"

    for r in result["results"]:
        assert "platform" in r
        assert "platform_name" in r
        assert "status" in r
        assert "answer" in r
        assert "duration_ms" in r
        assert "screenshot_path" in r
        assert "error" in r


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_check_login_empty_platform():
    """测试 check_login 空平台参数校验"""
    from mcp_server import check_login

    result = await check_login.fn(platform="")
    assert result["is_logged_in"] is False


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_capture_screenshot_empty_platform():
    """测试 capture_screenshot 空平台参数校验"""
    from mcp_server import capture_screenshot

    result = await capture_screenshot.fn(platform="")
    assert "error" in result


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ask_ai_return_structure_completeness():
    """测试 ask_ai 返回结构完整性"""
    from mcp_server import ask_ai, get_manager

    mock_manager = AsyncMock()
    mock_manager.ask_question = AsyncMock(return_value={
        "success": False,
        "total_count": 2,
        "success_count": 1,
        "question": "测试",
        "results": [
            {
                "platform": "doubao", "platform_name": "豆包",
                "status": "success", "answer": "答案1",
                "duration_ms": 1000, "screenshot_path": "/tmp/s1.png",
                "error": None,
            },
            {
                "platform": "chatglm", "platform_name": "智谱清言",
                "status": "failed", "answer": None,
                "duration_ms": 120000, "screenshot_path": "/tmp/s2.png",
                "error": "超时",
            },
        ],
    })

    with patch("mcp_server.get_manager", return_value=mock_manager):
        result = await ask_ai.fn(question="测试", platforms=["doubao", "chatglm"])

    assert "success" in result
    assert "total_count" in result
    assert "success_count" in result
    assert "question" in result
    assert "results" in result

    for r in result["results"]:
        assert isinstance(r["platform"], str)
        assert isinstance(r["platform_name"], str)
        assert isinstance(r["status"], str)
        assert r["status"] in ("success", "failed")
        assert isinstance(r["duration_ms"], int)

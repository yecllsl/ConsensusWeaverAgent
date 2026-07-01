"""元宝适配器单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from adapters.yuanbao_adapter import YuanbaoAdapter


@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.url = "https://yuanbao.tencent.com/chat"
    return page


@pytest.fixture
def adapter(mock_page):
    return YuanbaoAdapter(page=mock_page)


def test_yuanbao_adapter_attributes(adapter):
    assert adapter.platform_id == "yuanbao"
    assert adapter.platform_name == "元宝"
    assert adapter.base_url == "https://yuanbao.tencent.com/chat"


@pytest.mark.asyncio
async def test_yuanbao_navigate_to_chat(adapter, mock_page):
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    await adapter.navigate_to_chat()
    mock_page.goto.assert_called_once()


@pytest.mark.asyncio
async def test_yuanbao_check_login_status_logged_in(adapter, mock_page):
    mock_page.url = "https://yuanbao.tencent.com/chat/123"
    mock_page.query_selector = AsyncMock(return_value=MagicMock())
    result = await adapter.check_login_status()
    assert result is True


@pytest.mark.asyncio
async def test_yuanbao_check_login_status_not_logged_in(adapter, mock_page):
    mock_page.url = "https://yuanbao.tencent.com/login"
    mock_page.query_selector = AsyncMock(return_value=None)
    result = await adapter.check_login_status()
    assert result is False


@pytest.mark.asyncio
async def test_yuanbao_send_question(adapter, mock_page):
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    mock_page.fill = AsyncMock()
    mock_page.keyboard = AsyncMock()
    await adapter.send_question("测试问题")
    mock_page.wait_for_selector.assert_called()


@pytest.mark.asyncio
async def test_yuanbao_capture_screenshot(adapter, mock_page):
    mock_page.screenshot = AsyncMock(return_value=None)
    result = await adapter.capture_screenshot("/tmp/test.png")
    assert result == "/tmp/test.png"

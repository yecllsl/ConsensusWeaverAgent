"""豆包适配器单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from adapters.doubao_adapter import DoubaoAdapter
from adapters.base_adapter import AdapterResult


@pytest.fixture
def mock_page():
    """模拟 Page 对象"""
    page = AsyncMock()
    page.url = "https://www.doubao.com/chat"
    return page


@pytest.fixture
def adapter(mock_page):
    """豆包适配器 fixture"""
    return DoubaoAdapter(page=mock_page)


def test_doubao_adapter_attributes(adapter):
    """测试豆包适配器属性"""
    assert adapter.platform_id == "doubao"
    assert adapter.platform_name == "豆包"
    assert adapter.base_url == "https://www.doubao.com"


@pytest.mark.asyncio
async def test_doubao_navigate_to_chat(adapter, mock_page):
    """测试导航到聊天页"""
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())

    await adapter.navigate_to_chat()
    mock_page.goto.assert_called_once_with("https://www.doubao.com/chat", wait_until="domcontentloaded")


@pytest.mark.asyncio
async def test_doubao_check_login_status_logged_in(adapter, mock_page):
    """测试已登录状态检测：无登录按钮且输入框可见"""
    mock_page.url = "https://www.doubao.com/chat/123"
    textarea_mock = MagicMock()
    textarea_mock.is_visible = AsyncMock(return_value=True)
    # 前 3 次为登录按钮选择器（均未找到），第 4 次为 textarea
    mock_page.query_selector = AsyncMock(side_effect=[None, None, None, textarea_mock])

    result = await adapter.check_login_status()
    assert result is True


@pytest.mark.asyncio
async def test_doubao_check_login_status_not_logged_in(adapter, mock_page):
    """测试未登录状态检测"""
    mock_page.url = "https://www.doubao.com"
    mock_page.query_selector = AsyncMock(return_value=None)

    result = await adapter.check_login_status()
    assert result is False


@pytest.mark.asyncio
async def test_doubao_send_question(adapter, mock_page):
    """测试发送问题"""
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    mock_page.fill = AsyncMock()
    mock_page.keyboard = AsyncMock()

    await adapter.send_question("测试问题")
    mock_page.wait_for_selector.assert_called()


@pytest.mark.asyncio
async def test_doubao_capture_screenshot(adapter, mock_page):
    """测试截图"""
    mock_page.screenshot = AsyncMock(return_value=None)

    result = await adapter.capture_screenshot("/tmp/test.png")
    assert result == "/tmp/test.png"
    mock_page.screenshot.assert_called_once()

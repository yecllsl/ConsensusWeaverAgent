"""DeepSeek 适配器单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from adapters.deepseek_adapter import DeepSeekAdapter


@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.url = "https://chat.deepseek.com/chat"
    return page


@pytest.fixture
def adapter(mock_page):
    return DeepSeekAdapter(page=mock_page)


def test_deepseek_adapter_attributes(adapter):
    assert adapter.platform_id == "deepseek"
    assert adapter.platform_name == "DeepSeek"
    assert adapter.base_url == "https://chat.deepseek.com"


@pytest.mark.asyncio
async def test_deepseek_navigate_to_chat(adapter, mock_page):
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    await adapter.navigate_to_chat()
    mock_page.goto.assert_called_once()


def _make_visible_textarea():
    el = MagicMock()
    el.get_attribute = AsyncMock(return_value=None)
    el.is_visible = AsyncMock(return_value=True)
    el.click = AsyncMock()
    el.fill = AsyncMock()
    return el


@pytest.mark.asyncio
async def test_deepseek_check_login_status_logged_in(adapter, mock_page):
    mock_page.url = "https://chat.deepseek.com/chat/123"
    mock_page.query_selector_all = AsyncMock(return_value=[_make_visible_textarea()])
    result = await adapter.check_login_status()
    assert result is True


@pytest.mark.asyncio
async def test_deepseek_check_login_status_not_logged_in(adapter, mock_page):
    mock_page.url = "https://chat.deepseek.com/sign_in"
    mock_page.query_selector_all = AsyncMock(return_value=[])
    result = await adapter.check_login_status()
    assert result is False


@pytest.mark.asyncio
async def test_deepseek_send_question(adapter, mock_page):
    textarea = _make_visible_textarea()
    mock_page.query_selector_all = AsyncMock(return_value=[textarea])
    mock_page.keyboard = AsyncMock()
    await adapter.send_question("测试问题")
    textarea.click.assert_called_once()
    textarea.fill.assert_called_once_with("测试问题")


@pytest.mark.asyncio
async def test_deepseek_capture_screenshot(adapter, mock_page):
    mock_page.screenshot = AsyncMock(return_value=None)
    result = await adapter.capture_screenshot("/tmp/test.png")
    assert result == "/tmp/test.png"

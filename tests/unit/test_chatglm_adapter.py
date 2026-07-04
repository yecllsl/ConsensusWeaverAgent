"""智谱清言适配器单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from adapters.chatglm_adapter import ChatGLMAdapter


@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.url = "https://chatglm.cn/main/alltoolsdetail"
    return page


@pytest.fixture
def adapter(mock_page):
    return ChatGLMAdapter(page=mock_page)


def test_chatglm_adapter_attributes(adapter):
    assert adapter.platform_id == "chatglm"
    assert adapter.platform_name == "智谱清言"
    assert adapter.base_url == "https://chatglm.cn"


@pytest.mark.asyncio
async def test_chatglm_navigate_to_chat(adapter, mock_page):
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
async def test_chatglm_check_login_status_logged_in(adapter, mock_page):
    mock_page.url = "https://chatglm.cn/main/alltoolsdetail"
    mock_page.query_selector_all = AsyncMock(return_value=[_make_visible_textarea()])
    mock_page.query_selector = AsyncMock(return_value=None)
    result = await adapter.check_login_status()
    assert result is True


@pytest.mark.asyncio
async def test_chatglm_check_login_status_not_logged_in(adapter, mock_page):
    mock_page.url = "https://chatglm.cn/login"
    mock_page.query_selector_all = AsyncMock(return_value=[])
    result = await adapter.check_login_status()
    assert result is False


@pytest.mark.asyncio
async def test_chatglm_send_question(adapter, mock_page):
    textarea = _make_visible_textarea()
    mock_page.query_selector_all = AsyncMock(return_value=[textarea])
    mock_page.keyboard = AsyncMock()
    await adapter.send_question("测试问题")
    textarea.click.assert_called_once()
    textarea.fill.assert_called_once_with("测试问题")


@pytest.mark.asyncio
async def test_chatglm_capture_screenshot(adapter, mock_page):
    mock_page.screenshot = AsyncMock(return_value=None)
    result = await adapter.capture_screenshot("/tmp/test.png")
    assert result == "/tmp/test.png"


def test_chatglm_is_reasoning_text(adapter):
    """测试能识别智谱搜索推理/意图说明文本"""
    assert adapter._is_reasoning_text("用户询问如何提高代码质量，我将搜索相关资料")
    assert adapter._is_reasoning_text("用户要求给出可落地的建议，以便提炼出最佳实践")
    assert adapter._is_reasoning_text("我已经收集到大量信息。现在来组织答案，采用结构化方式。")
    assert adapter._is_reasoning_text("我将引用相关资料。现在开始构建答案。")
    assert adapter._is_reasoning_text("用户问的是强化学习是什么，以及一个现实世界中的应用例子。我需要先搜索。")
    assert not adapter._is_reasoning_text("提高团队代码质量的三条建议：代码审查、自动化测试、持续集成。")


def test_chatglm_strip_source_references(adapter):
    """测试能移除答案中混入的来源域名和 +N 标记（末尾和内联）"""
    text = "提高团队代码质量需要代码审查。\n\n51cto.com"
    assert adapter._strip_source_references(text) == "提高团队代码质量需要代码审查。"
    # 多行来源引用（域名 + +N 标记）
    text2 = "量子计算适合模拟量子系统。\n\nibm.com\n+2\n。"
    result = adapter._strip_source_references(text2)
    assert "ibm.com" not in result
    assert "+2" not in result
    assert "量子计算适合模拟量子系统" in result
    # 内联来源引用（段落中间）
    text3 = "长期阅读习惯靠环境设计\nzhihu.com\n+1\n。下面给出具体方案。"
    result3 = adapter._strip_source_references(text3)
    assert "zhihu.com" not in result3
    assert "+1" not in result3
    assert "环境设计。下面给出具体方案" in result3
    assert adapter._strip_source_references("没有来源引用的答案。") == "没有来源引用的答案。"

"""千问适配器单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from adapters.qianwen_adapter import QianwenAdapter


@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.url = "https://qianwen.com/chat"
    return page


@pytest.fixture
def adapter(mock_page):
    return QianwenAdapter(page=mock_page)


def test_qianwen_adapter_attributes(adapter):
    assert adapter.platform_id == "qianwen"
    assert adapter.platform_name == "千问"
    assert adapter.base_url == "https://qianwen.com/chat"


@pytest.mark.asyncio
async def test_qianwen_navigate_to_chat(adapter, mock_page):
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    await adapter.navigate_to_chat()
    mock_page.goto.assert_called_once()


@pytest.mark.asyncio
async def test_qianwen_check_login_status_logged_in(adapter, mock_page):
    mock_page.url = "https://qianwen.com/chat"
    mock_page.query_selector = AsyncMock(return_value=MagicMock())
    result = await adapter.check_login_status()
    assert result is True


@pytest.mark.asyncio
async def test_qianwen_check_login_status_not_logged_in(adapter, mock_page):
    mock_page.url = "https://qianwen.com/login"
    mock_page.query_selector = AsyncMock(return_value=None)
    result = await adapter.check_login_status()
    assert result is False


@pytest.mark.asyncio
async def test_qianwen_send_question(adapter, mock_page):
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    mock_page.fill = AsyncMock()
    mock_page.keyboard = AsyncMock()
    await adapter.send_question("测试问题")
    mock_page.wait_for_selector.assert_called()


@pytest.mark.asyncio
async def test_qianwen_capture_screenshot(adapter, mock_page):
    mock_page.screenshot = AsyncMock(return_value=None)
    result = await adapter.capture_screenshot("/tmp/test.png")
    assert result == "/tmp/test.png"


def test_qianwen_strip_recommendations(adapter):
    """测试能去除千问答案尾部混入的推荐视频/笔记列表"""
    text = (
        "提高团队代码质量需要代码审查。\n\n"
        "如何提升代码的质量\n\n"
        "麦哲思科技\n\n"
        "代码质量，从命名、函数、类、注释、测试、Git提交、坏...\n\n"
        "养生补给机"
    )
    result = adapter._strip_recommendations(text)
    assert "麦哲思科技" not in result
    assert "养生补给机" not in result
    assert "提高团队代码质量需要代码审查" in result


def test_qianwen_strip_recommendations_bilibili_style(adapter):
    """测试能去除B站风格的推荐标题+作者"""
    text = (
        "高效学习新编程语言需要项目驱动。\n\n"
        "升职加薪！新手程序员如何高效快速提升编程能力？\n\n"
        "快跑啊小卢_"
    )
    result = adapter._strip_recommendations(text)
    assert "快跑啊小卢_" not in result
    assert "新手程序员" not in result
    assert "高效学习新编程语言需要项目驱动" in result


def test_qianwen_strip_recommendations_title_marker_only(adapter):
    """测试标题有明显标识但作者无标识时也能过滤"""
    text = (
        "量子计算适合解决组合优化问题。\n\n"
        "第15期-量子计算机算力碾压，解决三大无解难题！\n\n"
        "子逸先生的漫步人生"
    )
    result = adapter._strip_recommendations(text)
    assert "子逸先生的漫步人生" not in result
    assert "第15期" not in result
    assert "量子计算适合解决组合优化问题" in result


def test_qianwen_strip_recommendations_multi_pairs_no_marker(adapter):
    """测试底部连续多对无明显标识的推荐也能过滤"""
    text = (
        "丝绸之路是东西方文化交流的重要通道。\n\n"
        "丝绸之路：东西方文明的交汇之路\n\n"
        "千秋史话堂\n\n"
        "古代丝绸之路上的文化交流与影响\n\n"
        "小狐狸346640781\n\n"
        "了不起的“丝绸之路”\n\n"
        "热爱自由的一片叶子"
    )
    result = adapter._strip_recommendations(text)
    assert "千秋史话堂" not in result
    assert "小狐狸346640781" not in result
    assert "热爱自由的一片叶子" not in result
    assert "丝绸之路是东西方文化交流的重要通道" in result


def test_qianwen_strip_recommendations_short_title_length_8(adapter):
    """测试标题长度恰好为 8 的推荐也能过滤"""
    text = (
        "培养和保持长期阅读习惯需要降低启动门槛。\n\n"
        "如何养成阅读习惯\n\n"
        "AI职场人阿欢"
    )
    result = adapter._strip_recommendations(text)
    assert "AI职场人阿欢" not in result
    assert "如何养成阅读习惯" not in result
    assert "培养和保持长期阅读习惯需要降低启动门槛" in result


def test_qianwen_strip_recommendations_long_title(adapter):
    """测试标题长度超过 80 的推荐也能过滤"""
    text = (
        "强化学习是机器学习的重要范式。\n\n"
        "机器学习、深度学习、强化学习之间的区别是什么？有监督、无监督、自监督的作用是什么？机器学习算法课程从入门到精通\n\n"
        "人工智能程序员"
    )
    result = adapter._strip_recommendations(text)
    assert "人工智能程序员" not in result
    assert "机器学习算法课程从入门到精通" not in result
    assert "强化学习是机器学习的重要范式" in result


def test_qianwen_strip_recommendations_strong_block_no_marker(adapter):
    """测试底部连续 >=3 对无明显标识的推荐块能整体过滤"""
    text = (
        "远程办公是一把双刃剑。\n\n"
        "企业数字化转型远程协作破局之策\n\n"
        "邑泊软件\n\n"
        "为什么优秀的职场人远程办公的效率更高\n\n"
        "金宝哥扯扯淡\n\n"
        "远程办公企业如何监管\n\n"
        "办公解忧屋"
    )
    result = adapter._strip_recommendations(text)
    assert "邑泊软件" not in result
    assert "金宝哥扯扯淡" not in result
    assert "办公解忧屋" not in result
    assert "远程办公是一把双刃剑" in result


def test_qianwen_strip_recommendations_mars_real_case(adapter):
    """测试火星移民问题中千问底部大量推荐列表能整体过滤"""
    text = (
        "简单来说，物质上的自给自足、生理上的环境适应、心理上的社会韧性，这三者缺一不可。"
        "你觉得在这三个问题里，哪一个是最难在短期内突破的？\n\n"
        "移民月球或火星的技术挑战本质上是，文明对自身脆弱性的终极抗争\n\n"
        "这就是机器人\n\n"
        "为什么说100年内人类做不到火星殖民\n\n"
        "十十万个都知道\n\n"
        "火星移民：人类文明的火种与生存挑战\n\n"
        "科学知音\n\n"
        "移民火星：人类未来的真实挑战\n\n"
        "宇宙科学探索\n\n"
        "如果人类想实现移民火星，需要做什么呢？，\n\n"
        "太空探索\n\n"
        "火星移民的技术挑战：地下海洋与升温改造的现实困境\n\n"
        "科技人生\n\n"
        "太空殖民计划：火星移民的现实困境 科学技术史·科技伦理挑战，第九集\n\n"
        "B站科普学院\n\n"
        "人类社会移民火星？这是对科学技术的重大考验。\n\n"
        "大蛤ge\n\n"
        "火星适合人类居住吗，答案：不适合\n\n"
        "蒲团静坐术\n\n"
        "#宇宙 #探索宇宙 #火星#移民 #关注我每天分享不同的故事\n\n"
        "敏锐昌吉7T9"
    )
    result = adapter._strip_recommendations(text)
    assert "敏锐昌吉7T9" not in result
    assert "蒲团静坐术" not in result
    assert "科学知音" not in result
    assert "人类社会移民火星" not in result
    assert "物质上的自给自足、生理上的环境适应、心理上的社会韧性" in result
    assert "你觉得在这三个问题里" in result

"""浏览器池集成测试 - 使用真实 Playwright 浏览器"""
import pytest
from pathlib import Path

from core.browser_pool import BrowserPool


@pytest.mark.integration
@pytest.mark.asyncio
async def test_browser_pool_start_stop(test_config):
    """测试浏览器池启动和停止"""
    pool = BrowserPool(test_config.browser)
    await pool.start()
    assert pool._playwright is not None

    await pool.stop()
    assert pool._playwright is None
    assert len(pool._contexts) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_browser_pool_get_context(test_config):
    """测试获取浏览器上下文"""
    pool = BrowserPool(test_config.browser)
    try:
        context = await pool.get_context("doubao", headless=True)
        assert context is not None
        assert "doubao" in pool._contexts

        context2 = await pool.get_context("doubao")
        assert context2 is context
    finally:
        await pool.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_browser_pool_get_page(test_config):
    """测试获取页面"""
    pool = BrowserPool(test_config.browser)
    try:
        page = await pool.get_page("doubao", headless=True)
        assert page is not None

        page2 = await pool.get_page("doubao")
        assert page2 is page
    finally:
        await pool.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_browser_pool_user_data_dir_created(test_config):
    """测试用户数据目录被创建"""
    pool = BrowserPool(test_config.browser)
    try:
        await pool.get_context("doubao", headless=True)
        user_data_path = Path(test_config.browser.user_data_base_dir) / "doubao"
        assert user_data_path.exists()
    finally:
        await pool.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_browser_pool_close_context(test_config):
    """测试关闭指定平台的上下文"""
    pool = BrowserPool(test_config.browser)
    try:
        await pool.get_context("doubao", headless=True)
        assert "doubao" in pool._contexts

        await pool.close_context("doubao")
        assert "doubao" not in pool._contexts
    finally:
        await pool.stop()

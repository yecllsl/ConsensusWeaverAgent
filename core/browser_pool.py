"""浏览器实例池，管理 Playwright 生命周期和用户数据目录"""
from pathlib import Path
from typing import Dict, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from core.config import BrowserConfig
from utils.logger import get_logger


class BrowserPool:
    """浏览器实例池

    管理多个浏览器上下文，每个平台使用独立的用户数据目录
    以持久化登录态（cookies、localStorage）。
    """

    def __init__(self, config: BrowserConfig):
        self.config = config
        self._playwright = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._pages: Dict[str, Page] = {}
        self.logger = get_logger("browser_pool")

    def _get_user_data_path(self, platform_id: str) -> str:
        """获取指定平台的用户数据目录路径"""
        return str(Path(self.config.user_data_base_dir) / platform_id)

    async def start(self) -> None:
        """启动 Playwright 运行时"""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            self.logger.info("Playwright 运行时已启动")

    async def stop(self) -> None:
        """关闭所有浏览器上下文和 Playwright 运行时"""
        for platform_id, page in self._pages.items():
            try:
                await page.close()
            except Exception as e:
                self.logger.warning(f"关闭页面 {platform_id} 失败: {e}")
        self._pages.clear()

        for platform_id, context in self._contexts.items():
            try:
                await context.close()
            except Exception as e:
                self.logger.warning(f"关闭上下文 {platform_id} 失败: {e}")
        self._contexts.clear()

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            self.logger.info("Playwright 运行时已停止")

    async def get_context(self, platform_id: str, headless: Optional[bool] = None) -> BrowserContext:
        """获取或创建指定平台的浏览器上下文"""
        if platform_id in self._contexts:
            return self._contexts[platform_id]

        if self._playwright is None:
            await self.start()

        user_data_path = self._get_user_data_path(platform_id)
        Path(user_data_path).mkdir(parents=True, exist_ok=True)

        is_headless = headless if headless is not None else self.config.headless

        context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            headless=is_headless,
            viewport={
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            slow_mo=self.config.slow_mo,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._contexts[platform_id] = context
        self.logger.info(f"为平台 {platform_id} 创建浏览器上下文")
        return context

    async def get_page(self, platform_id: str, headless: Optional[bool] = None) -> Page:
        """获取或创建指定平台的页面"""
        if platform_id in self._pages:
            try:
                _ = self._pages[platform_id].url
                return self._pages[platform_id]
            except Exception:
                del self._pages[platform_id]

        context = await self.get_context(platform_id, headless)

        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()

        self._pages[platform_id] = page
        return page

    async def close_context(self, platform_id: str) -> None:
        """关闭指定平台的浏览器上下文"""
        if platform_id in self._pages:
            try:
                await self._pages[platform_id].close()
            except Exception:
                pass
            del self._pages[platform_id]

        if platform_id in self._contexts:
            try:
                await self._contexts[platform_id].close()
            except Exception:
                pass
            del self._contexts[platform_id]
            self.logger.info(f"已关闭平台 {platform_id} 的浏览器上下文")

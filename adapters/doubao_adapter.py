"""豆包平台适配器"""
import asyncio
from typing import Optional

from playwright.async_api import Page

from adapters.base_adapter import BaseAdapter


class DoubaoAdapter(BaseAdapter):
    """豆包 (doubao.com) 适配器"""

    def __init__(self, page: Page):
        super().__init__(
            platform_id="doubao",
            platform_name="豆包",
            base_url="https://www.doubao.com",
        )
        self.page = page

    async def navigate_to_chat(self) -> None:
        """导航到豆包聊天页面"""
        await self.page.goto("https://www.doubao.com/chat", wait_until="domcontentloaded")
        await self.page.wait_for_selector("textarea", timeout=30000)
        self.logger.info("已导航到豆包聊天页")

    async def check_login_status(self) -> bool:
        """检查豆包登录状态，URL 和 DOM 双重判断"""
        checks_passed = 0
        if "/chat" in self.page.url:
            checks_passed += 1
        textarea = await self.page.query_selector("textarea")
        if textarea:
            checks_passed += 1
        self.logger.debug(f"豆包登录检测: {checks_passed}/2 项通过")
        return checks_passed >= 2

    async def send_question(self, question: str) -> None:
        """在豆包输入框中输入问题并发送"""
        textarea = await self.page.wait_for_selector("textarea", timeout=10000)
        await textarea.click()
        await self.page.fill("textarea", question)
        await self.page.keyboard.press("Enter")
        self.logger.info(f"已发送问题: {question[:50]}...")

    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待豆包回答完成并提取答案文本"""
        elapsed = 0
        poll_interval = 1
        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            textarea = await self.page.query_selector("textarea")
            if textarea:
                is_disabled = await textarea.get_attribute("disabled")
                if is_disabled is None:
                    await asyncio.sleep(2)
                    break
        answer = await self._extract_last_answer()
        if not answer:
            raise RuntimeError("未能提取到豆包的回答内容")
        self.logger.info(f"豆包回答已提取，长度: {len(answer)} 字符")
        return answer

    async def _extract_last_answer(self) -> Optional[str]:
        """提取最后一条 AI 回答文本"""
        selectors = [
            "[data-testid='receive_message']",
            ".message-assistant",
            ".chat-message-ai",
            "[class*='message-content']",
            "[class*='answer-content']",
            "[class*='markdown']",
        ]
        for selector in selectors:
            elements = await self.page.query_selector_all(selector)
            if elements:
                text = await elements[-1].inner_text()
                if text and len(text.strip()) > 0:
                    return text.strip()
        all_text = await self.page.evaluate("""() => {
            const messages = document.querySelectorAll('[class*="message"], [class*="chat"]');
            if (messages.length > 0) return messages[messages.length - 1].innerText;
            return '';
        }""")
        return all_text.strip() if all_text else None

    async def capture_screenshot(self, save_path: str) -> str:
        """截取豆包当前页面"""
        await self.page.screenshot(path=save_path, full_page=False)
        return save_path

    async def new_chat(self) -> None:
        """开启新的豆包对话"""
        try:
            new_chat_selectors = [
                "button:has-text('新对话')",
                "button:has-text('新建聊天')",
                "[class*='new-chat']",
                "[class*='new-conversation']",
            ]
            for selector in new_chat_selectors:
                btn = await self.page.query_selector(selector)
                if btn:
                    await btn.click()
                    await self.page.wait_for_timeout(1000)
                    self.logger.info("已通过按钮开启新对话")
                    return
        except Exception:
            pass
        await self.page.reload(wait_until="domcontentloaded")
        await self.page.wait_for_selector("textarea", timeout=15000)
        self.logger.info("已通过刷新页面开启新对话")

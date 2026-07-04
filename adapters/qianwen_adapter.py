"""千问平台适配器"""
import asyncio
from typing import Optional

from playwright.async_api import Page

from adapters.base_adapter import BaseAdapter


class QianwenAdapter(BaseAdapter):
    """千问 (qianwen.com) 适配器

    千问使用 contenteditable div 作为输入框，而不是 textarea，
    因此输入元素选择器需要同时兼容 textarea 和 contenteditable。
    """

    INPUT_SELECTOR = "textarea, [contenteditable='true'], [role='textbox']"

    def __init__(self, page: Page):
        super().__init__(
            platform_id="qianwen",
            platform_name="千问",
            base_url="https://qianwen.com/chat",
        )
        self.page = page

    async def navigate_to_chat(self) -> None:
        """导航到千问聊天页面"""
        await self.page.goto("https://qianwen.com/chat", wait_until="domcontentloaded")
        await self.page.wait_for_selector(self.INPUT_SELECTOR, timeout=30000)
        self.logger.info("已导航到千问聊天页")

    async def check_login_status(self) -> bool:
        """检查千问登录状态"""
        checks_passed = 0
        if "chat" in self.page.url and "login" not in self.page.url:
            checks_passed += 1
        input_el = await self.page.query_selector(self.INPUT_SELECTOR)
        if input_el:
            checks_passed += 1
        self.logger.debug(f"千问登录检测: {checks_passed}/2 项通过")
        return checks_passed >= 2

    async def send_question(self, question: str) -> None:
        """在千问输入框中输入问题并发送"""
        input_el = await self.page.wait_for_selector(self.INPUT_SELECTOR, timeout=10000)
        await input_el.click()
        await self.page.fill(self.INPUT_SELECTOR, question)
        await self.page.keyboard.press("Enter")
        self.logger.info(f"已发送问题: {question[:50]}...")

    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待千问回答完成并提取答案"""
        elapsed = 0
        poll_interval = 1
        last_len = -1
        stable_count = 0
        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            input_el = await self.page.query_selector(self.INPUT_SELECTOR)
            if input_el:
                tag = await input_el.evaluate("el => el.tagName")
                input_ready = False
                if tag.lower() == "textarea":
                    is_disabled = await input_el.get_attribute("disabled")
                    input_ready = is_disabled is None
                else:
                    editable = await input_el.get_attribute("contenteditable")
                    input_ready = editable is not None and editable.lower() != "false"

                # 输入框可用且答案长度稳定，才认为回答完成
                if input_ready:
                    current_answer = await self._extract_last_answer() or ""
                    current_len = len(current_answer)
                    if current_len > 0 and current_len == last_len:
                        stable_count += 1
                        if stable_count >= 3:
                            await asyncio.sleep(2)
                            break
                    else:
                        last_len = current_len
                        stable_count = 0
        answer = await self._extract_last_answer()
        if not answer:
            raise RuntimeError("未能提取到千问的回答内容")
        self.logger.info(f"千问回答已提取，长度: {len(answer)} 字符")
        return answer

    async def _extract_last_answer(self) -> Optional[str]:
        """提取最后一条 AI 回答文本"""
        selectors = [
            "[class*='answer']",
            "[class*='ai-message']",
            "[class*='markdown-body']",
            "[class*='message-content']",
            "[class*='response']",
            "[class*='chatRoom']",
            "[class*='bot']",
            "[class*='assistant']",
        ]
        for selector in selectors:
            elements = await self.page.query_selector_all(selector)
            for el in reversed(elements):
                try:
                    text = await el.inner_text()
                    text = text.strip()
                    if len(text) > 10:
                        return text
                except Exception:
                    continue
        all_text = await self.page.evaluate("""() => {
            const messages = document.querySelectorAll('[class*="message"], [class*="chat"]');
            for (let i = messages.length - 1; i >= 0; i--) {
                const text = messages[i].innerText?.trim() || '';
                if (text.length > 10) return text;
            }
            return '';
        }""")
        return all_text.strip() if all_text else None

    async def capture_screenshot(self, save_path: str) -> str:
        """截取千问当前页面"""
        await self.page.screenshot(path=save_path, full_page=False)
        return save_path

    async def new_chat(self) -> None:
        """开启新的千问对话"""
        try:
            for selector in ["button:has-text('新对话')", "button:has-text('新建')", "[class*='new-chat']", "[class*='new-conversation']"]:
                btn = await self.page.query_selector(selector)
                if btn:
                    await btn.click()
                    await self.page.wait_for_timeout(1000)
                    self.logger.info("已通过按钮开启新对话")
                    return
        except Exception:
            pass
        await self.page.reload(wait_until="domcontentloaded")
        await self.page.wait_for_selector(self.INPUT_SELECTOR, timeout=15000)
        self.logger.info("已通过刷新页面开启新对话")

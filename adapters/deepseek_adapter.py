"""DeepSeek 平台适配器"""
import asyncio
from typing import Optional

from playwright.async_api import Page

from adapters.base_adapter import BaseAdapter


class DeepSeekAdapter(BaseAdapter):
    """DeepSeek (chat.deepseek.com) 适配器

    注意：DeepSeek 有「深度思考」功能，回答时会有思考过程。
    本适配器只提取最终答案，不包含思考过程。
    """

    def __init__(self, page: Page):
        super().__init__(
            platform_id="deepseek",
            platform_name="DeepSeek",
            base_url="https://chat.deepseek.com",
        )
        self.page = page

    async def _get_input_element(self):
        """获取可用的输入框元素（过滤掉隐藏/只读的 WAF/配置 textarea）"""
        # DeepSeek 在 headless 下可能渲染多个 textarea，取最后一个可见且可编辑的
        textareas = await self.page.query_selector_all("textarea")
        for textarea in reversed(textareas):
            try:
                readonly = await textarea.get_attribute("readonly")
                disabled = await textarea.get_attribute("disabled")
                visible = await textarea.is_visible()
                if visible and not readonly and disabled is None:
                    return textarea
            except Exception:
                continue
        return None

    async def navigate_to_chat(self) -> None:
        """导航到 DeepSeek 聊天页面"""
        await self.page.goto("https://chat.deepseek.com/chat", wait_until="domcontentloaded")
        # 等待真实输入框出现
        for _ in range(30):
            el = await self._get_input_element()
            if el:
                break
            await asyncio.sleep(1)
        self.logger.info("已导航到 DeepSeek 聊天页")

    async def check_login_status(self) -> bool:
        """检查 DeepSeek 登录状态"""
        checks_passed = 0
        if "chat" in self.page.url and "sign_in" not in self.page.url:
            checks_passed += 1
        textarea = await self._get_input_element()
        if textarea:
            checks_passed += 1
        self.logger.debug(f"DeepSeek 登录检测: {checks_passed}/2 项通过")
        return checks_passed >= 2

    async def send_question(self, question: str) -> None:
        """在 DeepSeek 输入框中输入问题并发送"""
        textarea = await self._get_input_element()
        if not textarea:
            raise RuntimeError("DeepSeek 未找到可用的输入框")
        await textarea.click()
        await textarea.fill(question)
        await self.page.keyboard.press("Enter")
        self.logger.info(f"已发送问题: {question[:50]}...")

    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待 DeepSeek 回答完成并提取答案"""
        elapsed = 0
        poll_interval = 1
        stop_btn_gone = False
        last_len = -1
        stable_count = 0

        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            # DeepSeek 用停止按钮检测回答是否完成
            stop_btn = await self.page.query_selector("[class*='stop'], [aria-label='Stop']")
            if not stop_btn:
                if not stop_btn_gone:
                    stop_btn_gone = True
                    continue
                # 停止按钮消失后，再检查答案长度是否稳定
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
            raise RuntimeError("未能提取到 DeepSeek 的回答内容")
        self.logger.info(f"DeepSeek 回答已提取，长度: {len(answer)} 字符")
        return answer

    async def _extract_last_answer(self) -> Optional[str]:
        """提取最后一条 AI 回答文本，跳过思考过程

        DeepSeek 的长回答通常被拆成多个 markdown 块，需要拼接完整内容。
        """
        # 1. 尝试拼接所有非思考 markdown 块
        markdown_elements = await self.page.query_selector_all("div[class*='markdown']:not([class*='think'])")
        if markdown_elements:
            parts = []
            for el in markdown_elements:
                try:
                    text = await el.inner_text()
                    text = text.strip()
                    if text and text not in parts:
                        parts.append(text)
                except Exception:
                    continue
            if parts:
                return "\n\n".join(parts)

        # 2. 兜底选择器
        selectors = [
            "[class*='answer-content']",
            "[class*='message-content']",
            "[class*='ai-message']",
            "[class*='response']",
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
        """截取 DeepSeek 当前页面"""
        await self.page.screenshot(path=save_path, full_page=False)
        return save_path

    async def new_chat(self) -> None:
        """开启新的 DeepSeek 对话"""
        try:
            for selector in ["button:has-text('新对话')", "button:has-text('New Chat')", "[class*='new-chat']", "[class*='new-conversation']"]:
                btn = await self.page.query_selector(selector)
                if btn:
                    await btn.click()
                    await self.page.wait_for_timeout(1000)
                    self.logger.info("已通过按钮开启新对话")
                    return
        except Exception:
            pass
        await self.page.reload(wait_until="domcontentloaded")
        for _ in range(15):
            el = await self._get_input_element()
            if el:
                break
            await asyncio.sleep(1)
        self.logger.info("已通过刷新页面开启新对话")

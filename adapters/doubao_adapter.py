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
        """检查豆包登录状态

        判断逻辑：
        1. URL 包含 /chat
        2. 不存在明显的登录按钮（未登录标志）
        3. 页面有可交互的输入框
        """
        if "/chat" not in self.page.url:
            return False

        # 检查是否存在未登录的标志（明显的登录按钮/链接）
        login_selectors = [
            "button:has-text('登录')",
            "a:has-text('登录')",
            "[class*='login-btn']",
        ]
        for selector in login_selectors:
            try:
                el = await self.page.query_selector(selector)
                if el and await el.is_visible():
                    self.logger.debug(f"豆包未登录: 找到登录按钮 {selector}")
                    return False
            except Exception:
                pass

        # 检查是否存在可交互的输入框（登录后才能正常使用）
        try:
            textarea = await self.page.query_selector("textarea")
            if textarea and await textarea.is_visible():
                self.logger.debug("豆包已登录: 输入框可用")
                return True
        except Exception:
            pass

        self.logger.debug("豆包登录状态不确定")
        return False

    async def send_question(self, question: str) -> None:
        """在豆包输入框中输入问题并发送"""
        textarea = await self.page.wait_for_selector("textarea", timeout=10000)
        await textarea.click()
        await self.page.fill("textarea", question)
        await asyncio.sleep(0.5)

        # 优先点击发送按钮，失败则按 Enter
        sent = False
        send_selectors = [
            "button:has-text('发送')",
            "button[aria-label='发送']",
            "[class*='send-btn']",
            "[class*='submit-btn']",
            "button svg",
        ]
        for selector in send_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click()
                    sent = True
                    break
            except Exception:
                continue

        if not sent:
            # 尝试 Enter（部分平台用 Enter 发送）
            await self.page.keyboard.press("Enter")

        self.logger.info(f"已发送问题: {question[:50]}...")

    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待豆包回答完成并提取答案文本

        策略：先等待内容出现，再监测内容是否稳定（流式输出结束）
        """
        elapsed = 0
        poll_interval = 1
        last_answer = ""
        stable_count = 0
        stable_threshold = 3  # 连续3次内容不变则认为回答完成

        # 先等待 3 秒让 AI 开始回答
        await asyncio.sleep(3)
        elapsed = 3

        while elapsed < timeout:
            current_answer = await self._extract_last_answer() or ""
            if current_answer and current_answer != last_answer:
                # 内容还在变化，重置稳定计数
                last_answer = current_answer
                stable_count = 0
            elif current_answer and current_answer == last_answer:
                # 内容未变化
                stable_count += 1
                if stable_count >= stable_threshold:
                    break  # 连续3次不变，认为回答完成
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        if not last_answer:
            raise RuntimeError("未能提取到豆包的回答内容")
        self.logger.info(f"豆包回答已提取，长度: {len(last_answer)} 字符")
        return last_answer

    async def _extract_last_answer(self) -> Optional[str]:
        """提取最后一条 AI 回答文本

        策略：
        1. 先尝试常见的 data-testid / class 选择器
        2. 如果都失败，用问题文本作为锚点：找到用户问题在页面中的位置，
           然后找它后面最近的长文本元素（就是 AI 回答）
        """
        # 常见选择器尝试
        selectors = [
            "[data-testid='receive_message']",
            ".message-assistant",
            ".chat-message-ai",
            "[class*='message-content']",
            "[class*='answer-content']",
            "[class*='markdown-body']",
            "[class*='prose']",
            "article",
            "[data-streaming='false']",
            "[class*='md-box-root']",
            "[class*='container-']",
        ]
        for selector in selectors:
            elements = await self.page.query_selector_all(selector)
            if elements:
                for el in reversed(elements):
                    try:
                        text = await el.inner_text()
                        if text and len(text.strip()) > 10:
                            return text.strip()
                    except Exception:
                        continue

        # 兜底：豆包新版 DOM 中回答外层容器 class 形如 container-xxxxxx
        answer_text = await self.page.evaluate("""() => {
            const elements = document.querySelectorAll('[class*="container-"]');
            let lastText = '';
            for (let el of elements) {
                const text = el.innerText?.trim() || '';
                if (text.length > lastText.length && text.length > 15) {
                    lastText = text;
                }
            }
            return lastText || null;
        }""")

        return answer_text.strip() if answer_text else None

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
                if btn and await btn.is_visible():
                    await btn.click()
                    await self.page.wait_for_timeout(1000)
                    self.logger.info("已开启新对话")
                    return
        except Exception:
            pass
        self.logger.info("未找到新对话按钮，使用当前对话")

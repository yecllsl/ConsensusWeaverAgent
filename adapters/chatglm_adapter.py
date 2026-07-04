"""智谱清言平台适配器"""
import asyncio
from typing import Optional

from playwright.async_api import Page

from adapters.base_adapter import BaseAdapter


class ChatGLMAdapter(BaseAdapter):
    """智谱清言 (chatglm.cn) 适配器"""

    def __init__(self, page: Page):
        super().__init__(
            platform_id="chatglm",
            platform_name="智谱清言",
            base_url="https://chatglm.cn",
        )
        self.page = page

    async def _get_input_element(self):
        """获取可用的输入框元素（过滤隐藏/只读的 WAF textarea）"""
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
        """导航到智谱清言聊天页面"""
        await self.page.goto("https://chatglm.cn/main/alltoolsdetail", wait_until="domcontentloaded")
        for _ in range(30):
            el = await self._get_input_element()
            if el:
                break
            await asyncio.sleep(1)
        self.logger.info("已导航到智谱清言聊天页")

    async def check_login_status(self) -> bool:
        """检查智谱清言登录状态"""
        checks_passed = 0
        if "main" in self.page.url and "login" not in self.page.url:
            checks_passed += 1
        textarea = await self._get_input_element()
        if textarea:
            checks_passed += 1
        # 智谱清言可能会话过期后弹出登录框，检测到登录框视为未登录
        for login_text in ["微信扫码登录", "手机号登录"]:
            try:
                login_modal = await self.page.query_selector(f"text={login_text}")
                if login_modal and await login_modal.is_visible():
                    self.logger.debug("智谱清言检测到登录弹窗，视为未登录")
                    return False
            except Exception:
                continue
        self.logger.debug(f"智谱清言登录检测: {checks_passed}/2 项通过")
        return checks_passed >= 2

    async def send_question(self, question: str) -> None:
        """在智谱清言输入框中输入问题并发送"""
        textarea = await self._get_input_element()
        if not textarea:
            raise RuntimeError("智谱清言未找到可用的输入框")
        await textarea.click()
        await textarea.fill(question)
        await self.page.keyboard.press("Enter")
        self.logger.info(f"已发送问题: {question[:50]}...")

    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待智谱清言回答完成并提取答案"""
        elapsed = 0
        poll_interval = 1
        last_len = -1
        stable_count = 0
        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            # 输入框可用且答案长度稳定、非搜索状态，认为回答完成
            textarea = await self._get_input_element()
            if textarea:
                is_disabled = await textarea.get_attribute("disabled")
                if is_disabled is None:
                    current_answer = await self._extract_last_answer() or ""
                    current_len = len(current_answer)
                    # 搜索中/过短的内容不算有效完成
                    if current_len > 30 and current_len == last_len:
                        stable_count += 1
                        if stable_count >= 3:
                            await asyncio.sleep(2)
                            break
                    else:
                        last_len = current_len
                        stable_count = 0
        answer = await self._extract_last_answer()
        if not answer:
            raise RuntimeError("未能提取到智谱清言的回答内容")
        self.logger.info(f"智谱清言回答已提取，长度: {len(answer)} 字符")
        return answer

    def _is_searching_text(self, text: str) -> bool:
        """判断文本是否为智谱搜索状态提示"""
        return "搜索中" in text or "个来源" in text

    async def _extract_last_answer(self) -> Optional[str]:
        """提取最后一条 AI 回答文本，过滤平台名/短文本/搜索状态"""
        selectors = [
            # 优先使用聊天消息专用容器，避免匹配到设置/表单中的 answer/content-area
            "[class*='message-content']",
            "[class*='markdown-body']",
            "[class*='ai-message']",
            "[class*='chat-message']",
            "[class*='answer-content']",
        ]
        for selector in selectors:
            elements = await self.page.query_selector_all(selector)
            for el in reversed(elements):
                try:
                    text = await el.inner_text()
                    text = text.strip()
                    # 过滤过短、平台名、搜索中的无效文本
                    if len(text) > 30 and text.lower() != "chatglm" and not self._is_searching_text(text):
                        return text
                except Exception:
                    continue
        all_text = await self.page.evaluate("""() => {
            const messages = document.querySelectorAll('[class*="message-content"], [class*="markdown-body"], [class*="chat-message"]');
            for (let i = messages.length - 1; i >= 0; i--) {
                const text = messages[i].innerText?.trim() || '';
                if (text.length > 30 && text.toLowerCase() !== 'chatglm' && !text.includes('搜索中') && !text.includes('个来源')) return text;
            }
            return '';
        }""")
        return all_text.strip() if all_text else None

    async def capture_screenshot(self, save_path: str) -> str:
        """截取智谱清言当前页面"""
        await self.page.screenshot(path=save_path, full_page=False)
        return save_path

    async def new_chat(self) -> None:
        """开启新的智谱清言对话"""
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
        for _ in range(15):
            el = await self._get_input_element()
            if el:
                break
            await asyncio.sleep(1)
        self.logger.info("已通过刷新页面开启新对话")

"""元宝平台适配器"""
import asyncio
from typing import Optional

from playwright.async_api import Page

from adapters.base_adapter import BaseAdapter


class YuanbaoAdapter(BaseAdapter):
    """元宝 (yuanbao.tencent.com) 适配器

    注意：腾讯系产品可能有额外验证（如二维码登录确认），
    登录态检查需更严格。元宝输入框为 contenteditable div。
    """

    INPUT_SELECTOR = "[contenteditable='true'].ql-editor, textarea"

    def __init__(self, page: Page):
        super().__init__(
            platform_id="yuanbao",
            platform_name="元宝",
            base_url="https://yuanbao.tencent.com/chat",
        )
        self.page = page

    async def navigate_to_chat(self) -> None:
        """导航到元宝聊天页面"""
        await self.page.goto("https://yuanbao.tencent.com/chat", wait_until="domcontentloaded")
        await self.page.wait_for_selector(self.INPUT_SELECTOR, timeout=30000)
        self.logger.info("已导航到元宝聊天页")

    async def check_login_status(self) -> bool:
        """检查元宝登录状态"""
        checks_passed = 0
        if "chat" in self.page.url and "login" not in self.page.url:
            checks_passed += 1
        input_el = await self.page.query_selector(self.INPUT_SELECTOR)
        if input_el:
            checks_passed += 1
        self.logger.debug(f"元宝登录检测: {checks_passed}/2 项通过")
        return checks_passed >= 2

    async def send_question(self, question: str) -> None:
        """在元宝输入框中输入问题并发送"""
        input_el = await self.page.wait_for_selector(self.INPUT_SELECTOR, timeout=10000)
        await input_el.click()
        await self.page.fill(self.INPUT_SELECTOR, question)
        await self.page.keyboard.press("Enter")
        self._last_question = question  # 记录问题文本，供答案提取时过滤
        self.logger.info(f"已发送问题: {question[:50]}...")

    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待元宝回答完成并提取答案"""
        elapsed = 0
        poll_interval = 1
        last_len = -1
        stable_count = 0
        last_question = getattr(self, "_last_question", "")

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

                # 输入框可用且答案长度稳定，且不是欢迎语，才认为回答完成
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
            raise RuntimeError("未能提取到元宝的回答内容")
        self.logger.info(f"元宝回答已提取，长度: {len(answer)} 字符")
        return answer

    def _is_welcome_text(self, text: str) -> bool:
        """判断文本是否为元宝欢迎语/引导语/侧边栏推荐

        注意：只过滤明确的欢迎面板或推荐列表，不拦截正常回答中
        出现的“我是元宝”等自我介绍。
        """
        # 明确的欢迎面板开头
        if text.startswith("Hi~ 我是元宝"):
            return True
        # 推荐/引导语特征：同时包含多个无关主题卡片
        suggestion_markers = ["元宝高考通", "下载元宝电脑版", "部分功能服务", "今天从哪里开始"]
        matched = sum(1 for m in suggestion_markers if m in text)
        if matched >= 2:
            return True
        # 典型引导语组合
        if "快来点击以下任一功能" in text or "你可以这样问" in text:
            return True
        return False

    async def _extract_last_answer(self) -> Optional[str]:
        """提取最后一条 AI 回答文本

        策略：
        1. 优先尝试 AI 消息专用选择器
        2. 从后往前遍历，过滤掉包含用户问题原文和欢迎语的元素
        3. 兜底使用通用 message/chat 元素
        """
        selectors = [
            # 元宝 AI 消息专用 class（按匹配精度排序）
            ".agent-chat__list__item--ai .agent-chat__bubble__content",
            ".agent-chat__list__item--ai",
            ".agent-chat__bubble--ai",
            ".agent-chat__bubble__content",
            ".hyc-content-md",
            # 通用兜底
            "[class*='ai-message']",
            "[class*='answer-content']",
            "[class*='agent-dialogue__content--common__content']",
            "[class*='agent-dialogue__content']",
            "[class*='markdown-body']",
            "[class*='message-content']",
            "[class*='answer']",
            "[class*='response']",
            "[class*='chat-content']",
        ]
        last_question = getattr(self, "_last_question", "")

        for selector in selectors:
            elements = await self.page.query_selector_all(selector)
            for el in reversed(elements):
                try:
                    text = await el.inner_text()
                    text = text.strip()
                    if not text:
                        continue
                    # 跳过包含用户问题的元素
                    if last_question and last_question in text:
                        continue
                    # 跳过欢迎语
                    if self._is_welcome_text(text):
                        continue
                    return text
                except Exception:
                    continue

        # 兜底：从通用消息元素中从后往前找第一条不含问题且非欢迎语的文本
        all_text = await self.page.evaluate(
            """(question) => {
                const messages = document.querySelectorAll('[class*="message"], [class*="chat"]');
                for (let i = messages.length - 1; i >= 0; i--) {
                    const text = messages[i].innerText?.trim() || '';
                    if (!text) continue;
                    if (question && text.includes(question)) continue;
                    if (text.startsWith('Hi~ 我是元宝')) continue;
                    const suggestionMarkers = ['元宝高考通', '下载元宝电脑版', '部分功能服务', '今天从哪里开始'];
                    if (suggestionMarkers.filter(m => text.includes(m)).length >= 2) continue;
                    if (text.includes('快来点击以下任一功能') || text.includes('你可以这样问')) continue;
                    return text;
                }
                return '';
            }""",
            last_question,
        )
        return all_text.strip() if all_text else None

    async def capture_screenshot(self, save_path: str) -> str:
        """截取元宝当前页面"""
        await self.page.screenshot(path=save_path, full_page=False)
        return save_path

    async def new_chat(self) -> None:
        """开启新的元宝对话"""
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

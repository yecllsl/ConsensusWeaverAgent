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

    def _strip_recommendations(self, text: str) -> str:
        """去除千问答案尾部混入的推荐视频/笔记列表

        推荐区通常表现为“标题 +（空行）+ 作者名”成对出现，作者行短且无标点；
        标题常为疑问/感叹句。从底部向上扫描并移除。
        """
        # 标题常见特征词/标点
        title_markers = ["如何", "什么", "吗", "？", "！", "招", "点", "误区", "陷阱",
                         "指南", "教程", "课程", "提升", "掌握", "学会", "逆袭", "自救",
                         "建议", "方法", "优化", "新手", "程序员", "入门", "零基础",
                         "快速", "高效"]
        # 作者常见标识
        author_markers = ["讲", "_", "老师", "官方", "面试", "营", "站", "科技", "编程",
                          "动力", "补给", "港湾", "研究员", "装置", "小卢", "奇哥",
                          "阿甘", "pink", "闻", "少年", "小白"]

        lines = text.split("\n")

        # 预扫描：从底部向上统计连续“标题 + 短作者”对数
        # 若底部存在明显的推荐块（>=3 对），则第一对可放宽判断
        def _count_bottom_pairs() -> int:
            pairs = 0
            i = len(lines) - 1
            while i >= 0:
                while i >= 0 and lines[i].strip() == "":
                    i -= 1
                if i < 0:
                    break
                author = lines[i].strip()
                if not (0 < len(author) < 20 and not any(c in author for c in "。，！？；：")):
                    break
                j = i - 1
                while j >= 0 and lines[j].strip() == "":
                    j -= 1
                if j < 0:
                    break
                title = lines[j].strip()
                if not (8 <= len(title) < 120):
                    break
                pairs += 1
                i = j - 1
            return pairs

        strong_recommendation_block = _count_bottom_pairs() >= 3

        removed_pairs = 0
        while True:
            # 1. 跳过尾部空行
            while lines and lines[-1].strip() == "":
                lines.pop()
            if not lines:
                break

            # 2. 按基本形态识别作者行（短、无标点）
            author_idx = len(lines) - 1
            author = lines[author_idx].strip()
            has_author_marker = any(m in author for m in author_markers)
            is_short_no_punct = (
                0 < len(author) < 20
                and not any(c in author for c in "。，！？；：")
            )
            if not is_short_no_punct:
                break

            # 3. 跳过作者行上方的空行，找到标题行
            title_idx = author_idx - 1
            while title_idx >= 0 and lines[title_idx].strip() == "":
                title_idx -= 1
            if title_idx < 0:
                break
            title = lines[title_idx].strip()
            has_title_marker = any(m in title for m in title_markers)
            # 第一对兜底：作者极短 + 标题含常见分隔符/书名号/引号，说明是视频/笔记标题
            has_title_separators = any(c in title for c in "：《》\"\"''·|—-“”‘’")
            first_pair_loose = removed_pairs == 0 and len(author) < 12 and has_title_separators
            # 标题长度合适，且本身有标识、或已识别过推荐、或当前作者有标识、
            # 或满足兜底条件、或底部已是明显推荐块
            # 上限放宽到 120：千问推荐标题可能很长
            looks_like_title = 8 <= len(title) < 120 and (
                has_title_marker or removed_pairs > 0 or has_author_marker or first_pair_loose or strong_recommendation_block
            )
            if not looks_like_title:
                break

            # 4. 移除标题到作者之间的所有行（含空行）
            del lines[title_idx:]
            removed_pairs += 1

        # 移除残留的尾部空行
        while lines and lines[-1].strip() == "":
            lines.pop()

        # 循环内已对第一对做安全检查，只要移除过推荐就应用过滤
        if removed_pairs >= 1:
            return "\n".join(lines)
        return text

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
                        return self._strip_recommendations(text)
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
        text = all_text.strip() if all_text else None
        return self._strip_recommendations(text) if text else None

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

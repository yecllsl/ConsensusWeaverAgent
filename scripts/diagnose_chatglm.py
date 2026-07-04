"""ChatGLM DOM 诊断脚本"""
import asyncio
import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from playwright.async_api import async_playwright
from adapters.chatglm_adapter import ChatGLMAdapter


async def main():
    user_data_dir = Path("d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\user_data\\chatglm")
    user_data_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        adapter = ChatGLMAdapter(page)

        await adapter.navigate_to_chat()
        print("登录状态:", await adapter.check_login_status())
        await adapter.new_chat()
        question = "解释一下什么是 REST API，并举一个实际例子。"
        await adapter.send_question(question)

        # 等待回答完成
        print("等待 25 秒让回答生成...")
        await asyncio.sleep(25)

        # 截图
        screenshot_path = "d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\screenshots\\chatglm_diagnose.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"截图已保存: {screenshot_path}")

        # 保存页面 HTML
        html = await page.content()
        html_path = "d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\chatglm_diagnose.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML 已保存: {html_path}")

        # 打印一些关键元素的 innerText
        selectors = [
            "[class*='message-content']",
            "[class*='markdown-body']",
            "[class*='ai-message']",
            "[class*='chat-message']",
            "[class*='answer-content']",
            "[class*='answer']",
            "[class*='content-area']",
        ]
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            print(f"\n选择器 {selector}: 匹配 {len(elements)} 个元素")
            for idx, el in enumerate(elements[-3:]):
                try:
                    text = await el.inner_text()
                    text = text.strip().replace("\n", " ")[:150]
                    print(f"  [{idx}] {text}")
                except Exception as e:
                    print(f"  [{idx}] 错误: {e}")

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())

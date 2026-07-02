"""页面 DOM 检查工具：定位输入框、发送按钮、消息/回答元素"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from playwright.async_api import async_playwright

PLATFORM_URLS = {
    "doubao": "https://www.doubao.com/chat",
    "deepseek": "https://chat.deepseek.com/chat",
    "chatglm": "https://chatglm.cn/main/alltoolsdetail",
    "qianwen": "https://qianwen.com/chat",
    "yuanbao": "https://yuanbao.tencent.com/chat",
}


async def inspect(platform_id: str):
    url = PLATFORM_URLS[platform_id]
    user_data_dir = Path(f"d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\user_data\\{platform_id}")
    user_data_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        print(f"导航到 {url}")
        await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print(f"URL: {page.url}")
        print(f"标题: {await page.title()}")

        # 输入类元素
        print("\n=== 输入类元素 ===")
        input_selectors = [
            "textarea",
            "input[type='text']",
            "[contenteditable='true']",
            "[contenteditable='']",
            "[role='textbox']",
        ]
        for sel in input_selectors:
            elements = await page.query_selector_all(sel)
            print(f"\n选择器 {sel}: {len(elements)} 个")
            for i, el in enumerate(elements[:5]):
                tag = await el.evaluate("el => el.tagName")
                cls = await el.get_attribute("class") or ""
                id_ = await el.get_attribute("id") or ""
                placeholder = await el.get_attribute("placeholder") or ""
                print(f"  [{i}] tag={tag} id={id_} class={cls[:80]} placeholder={placeholder[:40]}")

        # 发送按钮
        print("\n=== 发送按钮候选 ===")
        send_selectors = [
            "button:has-text('发送')",
            "button[aria-label='发送']",
            "[class*='send-btn']",
            "[class*='submit-btn']",
            "button svg",
            "button[type='submit']",
        ]
        for sel in send_selectors:
            elements = await page.query_selector_all(sel)
            print(f"选择器 {sel}: {len(elements)} 个")

        # 发送测试问题
        question = "你好，请用一句话介绍你自己"
        print(f"\n发送测试问题: {question}")
        textarea = await page.query_selector("textarea")
        if textarea:
            await textarea.click()
            await page.fill("textarea", question)
        else:
            editable = await page.query_selector("[contenteditable='true']")
            if editable:
                await editable.click()
                await page.fill("[contenteditable='true']", question)
        await page.keyboard.press("Enter")

        print("等待 8 秒让 AI 开始回答...")
        await asyncio.sleep(8)

        # 消息/回答元素
        print("\n=== 消息/回答元素 ===")
        message_selectors = [
            "[data-testid='receive_message']",
            ".message-assistant",
            ".chat-message-ai",
            "[class*='message-content']",
            "[class*='answer-content']",
            "[class*='markdown-body']",
            "[class*='prose']",
            "article",
            "[class*='message']",
            "[class*='chat']",
            "[class*='answer']",
        ]
        for sel in message_selectors:
            elements = await page.query_selector_all(sel)
            print(f"\n选择器 {sel}: {len(elements)} 个")
            for i, el in enumerate(elements[-3:]):
                try:
                    text = await el.inner_text()
                    cls = await el.get_attribute("class") or ""
                    print(f"  [{i}] class={cls[:80]}")
                    print(f"      文本: {text[:150].replace(chr(10), ' ')}")
                except Exception as e:
                    print(f"      获取文本失败: {e}")

        # 文本锚点：查找包含问题或典型回答关键词的元素
        print("\n=== 文本锚点元素 ===")
        for keyword in ["你好，请用一句话介绍你自己", "字节跳动", "AI", "腾讯", "混元", "DeepSeek", "智谱", "千问"]:
            elements = await page.query_selector_all(f"text={keyword}")
            if elements:
                print(f"\n关键词 '{keyword}' 找到 {len(elements)} 个元素")
                for i, el in enumerate(elements[:3]):
                    cls = await el.get_attribute("class") or ""
                    tag = await el.evaluate("e => e.tagName")
                    parent = await el.evaluate("e => { const p=e.parentElement; return p ? (p.className||'') : '' }")
                    print(f"  [{i}] <{tag}> class={cls[:80]} parent_class={parent[:80]}")
                    # 打印外层 3 级 HTML 片段
                    html = await el.evaluate("""e => {
                        let cur = e;
                        for (let i=0; i<3 && cur.parentElement; i++) cur = cur.parentElement;
                        return cur.outerHTML.slice(0, 600);
                    }""")
                    print(f"      外层 HTML: {html}")

        shot_path = f"d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\screenshots\\inspect_{platform_id}.png"
        await page.screenshot(path=shot_path, full_page=False)
        print(f"\n截图已保存: {shot_path}")
        await asyncio.sleep(10)
        await context.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("platform", choices=list(PLATFORM_URLS.keys()))
    args = parser.parse_args()
    print(f"PLAYWRIGHT_BROWSERS_PATH = {os.environ.get('PLAYWRIGHT_BROWSERS_PATH', '未设置')}")
    asyncio.run(inspect(args.platform))

"""5 平台综合测试脚本 - 多问题、低频次、带延迟"""
import argparse
import asyncio
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from playwright.async_api import async_playwright
from adapters.doubao_adapter import DoubaoAdapter
from adapters.deepseek_adapter import DeepSeekAdapter
from adapters.chatglm_adapter import ChatGLMAdapter
from adapters.qianwen_adapter import QianwenAdapter
from adapters.yuanbao_adapter import YuanbaoAdapter

ADAPTER_REGISTRY = {
    "doubao": (DoubaoAdapter, "豆包"),
    "deepseek": (DeepSeekAdapter, "DeepSeek"),
    "chatglm": (ChatGLMAdapter, "智谱清言"),
    "qianwen": (QianwenAdapter, "千问"),
    "yuanbao": (YuanbaoAdapter, "元宝"),
}

TEST_QUESTIONS = [
    "你好，请用一句话介绍你自己",
    "如何学习 Python 编程？请给出 3 条具体建议。",
    "解释一下什么是 REST API，并举一个实际例子。",
]


async def test_platform(platform_id: str, question: str, headless: bool = True):
    """测试单个平台回答一个问题"""
    adapter_cls, platform_name = ADAPTER_REGISTRY[platform_id]
    user_data_dir = Path(f"d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\user_data\\{platform_id}")
    user_data_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "platform": platform_id,
        "platform_name": platform_name,
        "question": question,
        "success": False,
        "answer": None,
        "answer_length": 0,
        "error": None,
        "duration_ms": 0,
        "screenshot": None,
    }

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=headless,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        adapter = adapter_cls(page)

        start = asyncio.get_event_loop().time()
        try:
            await adapter.navigate_to_chat()
            is_logged_in = await adapter.check_login_status()
            if not is_logged_in:
                raise RuntimeError(f"{platform_name} 未登录")
            await adapter.new_chat()
            await adapter.send_question(question)
            answer = await adapter.wait_for_answer(timeout=120)
            result["success"] = True
            result["answer"] = answer
            result["answer_length"] = len(answer)
        except Exception as e:
            result["error"] = str(e)

        elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
        result["duration_ms"] = elapsed

        screenshot_path = f"d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\screenshots\\test_{platform_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        try:
            await adapter.capture_screenshot(screenshot_path)
            result["screenshot"] = screenshot_path
        except Exception:
            pass

        await context.close()
        return result


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platforms", nargs="+", choices=list(ADAPTER_REGISTRY.keys()), default=list(ADAPTER_REGISTRY.keys()))
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--delay", type=int, default=10, help="平台间延迟（秒）")
    args = parser.parse_args()

    all_results = []
    for q_idx, question in enumerate(TEST_QUESTIONS):
        print(f"\n{'='*60}")
        print(f"问题 {q_idx+1}/{len(TEST_QUESTIONS)}: {question}")
        print(f"{'='*60}")

        for platform_id in args.platforms:
            # 每次调用前随机延迟，模拟人类操作节奏
            jitter = random.uniform(1, 3)
            print(f"\n[{platform_id}] 等待 {args.delay + jitter:.1f}s 后测试...")
            await asyncio.sleep(args.delay + jitter)

            result = await test_platform(platform_id, question, headless=args.headless)
            all_results.append(result)

            status = "✓" if result["success"] else "✗"
            preview = (result.get("answer") or "")[:80].replace("\n", " ")
            print(f"  {status} {platform_id:10s} | 长度 {result['answer_length']:4d} | 耗时 {result['duration_ms']}ms")
            print(f"     预览: {preview}")
            if result["error"]:
                print(f"     错误: {result['error']}")

    # 写报告
    report_dir = Path("d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\test_reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"all_platforms_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report = {
        "generated_at": datetime.now().isoformat(),
        "questions": TEST_QUESTIONS,
        "platforms": args.platforms,
        "results": all_results,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n测试报告已保存: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())

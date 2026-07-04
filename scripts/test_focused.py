"""聚焦测试：验证 DeepSeek、ChatGLM、元宝修复效果"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from playwright.async_api import async_playwright
from adapters.deepseek_adapter import DeepSeekAdapter
from adapters.chatglm_adapter import ChatGLMAdapter
from adapters.yuanbao_adapter import YuanbaoAdapter

ADAPTER_REGISTRY = {
    "deepseek": (DeepSeekAdapter, "DeepSeek"),
    "chatglm": (ChatGLMAdapter, "智谱清言"),
    "yuanbao": (YuanbaoAdapter, "元宝"),
}

TEST_CASES = [
    ("deepseek", "如何学习 Python 编程？请给出 3 条具体建议。"),
    ("deepseek", "解释一下什么是 REST API，并举一个实际例子。"),
    ("chatglm", "解释一下什么是 REST API，并举一个实际例子。"),
    ("yuanbao", "你好，请用一句话介绍你自己"),
]


async def test_platform(platform_id: str, question: str):
    adapter_cls, platform_name = ADAPTER_REGISTRY[platform_id]
    user_data_dir = Path(f"d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\user_data\\{platform_id}")
    user_data_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "platform": platform_id,
        "question": question,
        "success": False,
        "answer": None,
        "answer_length": 0,
        "error": None,
        "duration_ms": 0,
    }

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        adapter = adapter_cls(page)

        start = asyncio.get_event_loop().time()
        try:
            await adapter.navigate_to_chat()
            if not await adapter.check_login_status():
                raise RuntimeError(f"{platform_name} 未登录")
            await adapter.new_chat()
            await adapter.send_question(question)
            answer = await adapter.wait_for_answer(timeout=120)
            result["success"] = True
            result["answer"] = answer
            result["answer_length"] = len(answer)
        except Exception as e:
            result["error"] = str(e)

        result["duration_ms"] = int((asyncio.get_event_loop().time() - start) * 1000)
        await context.close()
        return result


async def main():
    results = []
    for platform_id, question in TEST_CASES:
        print(f"\n[{platform_id}] {question}")
        result = await test_platform(platform_id, question)
        results.append(result)
        status = "✓" if result["success"] else "✗"
        preview = (result.get("answer") or "")[:120].replace("\n", " ")
        print(f"  {status} 长度 {result['answer_length']:5d} | 耗时 {result['duration_ms']}ms")
        print(f"     预览: {preview}")
        if result["error"]:
            print(f"     错误: {result['error']}")
        await asyncio.sleep(5)

    report_path = Path("d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\test_reports") / f"focused_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())

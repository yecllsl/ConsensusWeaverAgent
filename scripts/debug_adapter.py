"""统一适配器调试脚本 - 支持全部 5 个平台单步验证与批量验证"""
import argparse
import asyncio
import json
import os
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
    "doubao": (DoubaoAdapter, "doubao"),
    "deepseek": (DeepSeekAdapter, "deepseek"),
    "chatglm": (ChatGLMAdapter, "chatglm"),
    "qianwen": (QianwenAdapter, "qianwen"),
    "yuanbao": (YuanbaoAdapter, "yuanbao"),
}


async def _dump_page_info(page, label: str):
    """异常时打印页面诊断信息并截图"""
    print(f"\n[!] {label}")
    print(f"    URL: {page.url}")
    try:
        title = await page.title()
        print(f"    标题: {title}")
    except Exception as e:
        print(f"    标题获取失败: {e}")

    textareas = await page.query_selector_all("textarea")
    print(f"    textarea 数量: {len(textareas)}")

    iframes = await page.query_selector_all("iframe")
    print(f"    iframe 数量: {len(iframes)}")
    for i, iframe in enumerate(iframes):
        src = await iframe.get_attribute("src")
        print(f"      iframe[{i}]: src={src}")

    report_dir = Path("d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\debug_reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    error_shot = str(report_dir / f"debug_{label}_error.png")
    try:
        await page.screenshot(path=error_shot, full_page=False)
        print(f"    异常截图: {error_shot}")
    except Exception as e:
        print(f"    截图失败: {e}")


async def debug_platform(platform_id: str, headless: bool = False):
    """调试单个平台，返回结构化结果"""
    if platform_id not in ADAPTER_REGISTRY:
        raise ValueError(f"不支持的平台: {platform_id}，可选: {list(ADAPTER_REGISTRY.keys())}")

    adapter_cls, data_dir_name = ADAPTER_REGISTRY[platform_id]
    user_data_dir = Path(f"d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\user_data\\{data_dir_name}")
    user_data_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "platform": platform_id,
        "success": False,
        "url": None,
        "login_status": None,
        "answer_length": 0,
        "answer_preview": "",
        "screenshot": None,
        "error": None,
        "started_at": datetime.now().isoformat(),
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

        print(f"\n=== 开始调试 {platform_id} ===")
        print(f"[1] 导航到聊天页...")
        try:
            await adapter.navigate_to_chat()
            result["url"] = page.url
            print(f"    当前 URL: {page.url}")
        except Exception as e:
            print(f"    导航失败: {e}")
            result["error"] = f"导航失败: {e}"
            await _dump_page_info(page, platform_id)
            await context.close()
            return result

        print(f"[2] 检查登录状态...")
        try:
            is_logged_in = await adapter.check_login_status()
            result["login_status"] = "logged_in" if is_logged_in else "not_logged_in"
            print(f"    登录状态: {'已登录' if is_logged_in else '未登录'}")
        except Exception as e:
            print(f"    登录检查异常: {e}")
            result["error"] = f"登录检查异常: {e}"
            await _dump_page_info(page, platform_id)
            await context.close()
            return result

        if not is_logged_in:
            print(f"    请在浏览器中完成登录，脚本暂停 60 秒...")
            await asyncio.sleep(60)
            is_logged_in = await adapter.check_login_status()
            result["login_status"] = "logged_in" if is_logged_in else "not_logged_in"
            print(f"    再次检查登录状态: {'已登录' if is_logged_in else '未登录'}")
            if not is_logged_in:
                print(f"[x] {platform_id} 仍未登录，结束调试")
                result["error"] = "未登录"
                await _dump_page_info(page, platform_id)
                await context.close()
                return result

        print(f"[3] 开启新对话...")
        try:
            await adapter.new_chat()
        except Exception as e:
            print(f"    开启新对话失败: {e}")

        question = "你好，请用一句话介绍你自己"
        print(f"[4] 发送测试问题: {question}")
        try:
            await adapter.send_question(question)
        except Exception as e:
            print(f"    发送问题失败: {e}")
            result["error"] = f"发送问题失败: {e}"
            await _dump_page_info(page, platform_id)
            await context.close()
            return result

        print(f"[5] 等待回答完成...")
        try:
            answer = await adapter.wait_for_answer(timeout=120)
            result["success"] = True
            result["answer_length"] = len(answer)
            result["answer_preview"] = answer[:200]
            print(f"[6] ✓ 回答提取成功，长度: {len(answer)} 字符")
            print(f"    内容预览: {answer[:200].replace(chr(10), ' ')}")
        except Exception as e:
            print(f"[6] ✗ 等待或提取回答失败: {e}")
            result["error"] = f"等待或提取回答失败: {e}"
            await _dump_page_info(page, platform_id)

        screenshot_path = f"d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\screenshots\\debug_{platform_id}_result.png"
        try:
            await adapter.capture_screenshot(screenshot_path)
            result["screenshot"] = screenshot_path
            print(f"[7] 截图已保存: {screenshot_path}")
        except Exception as e:
            print(f"[7] 截图保存失败: {e}")

        print(f"[8] {platform_id} 调试完成，浏览器将在 5 秒后关闭...")
        await asyncio.sleep(5)
        await context.close()
        return result


def _write_report(results: list):
    """将批量调试结果写入 JSON 报告"""
    report_dir = Path("d:\\yecll\\Documents\\LocalCode\\ConsensusWeaverAgent\\data\\debug_reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report = {
        "generated_at": datetime.now().isoformat(),
        "playwright_browsers_path": os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "未设置"),
        "total": len(results),
        "success_count": sum(1 for r in results if r["success"]),
        "results": results,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n调试报告已保存: {report_path}")
    return report_path


async def run_all(headless: bool = False):
    """顺序调试全部 5 个平台"""
    results = []
    for platform_id in list(ADAPTER_REGISTRY.keys()):
        result = await debug_platform(platform_id, headless=headless)
        results.append(result)
        # 平台之间短暂停顿，确保浏览器进程完全释放
        await asyncio.sleep(3)
    _write_report(results)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="调试指定 AI 平台适配器")
    parser.add_argument("platform", nargs="?", choices=list(ADAPTER_REGISTRY.keys()), help="要调试的平台")
    parser.add_argument("--all", action="store_true", help="顺序调试全部平台")
    parser.add_argument("--headless", action="store_true", help="是否使用无头模式")
    args = parser.parse_args()

    if not args.platform and not args.all:
        parser.error("请指定 platform 或使用 --all")

    print(f"PLAYWRIGHT_BROWSERS_PATH = {os.environ.get('PLAYWRIGHT_BROWSERS_PATH', '未设置')}")

    if args.all:
        results = asyncio.run(run_all(headless=args.headless))
        success_count = sum(1 for r in results if r["success"])
        print(f"\n全部平台调试完成: {success_count}/{len(results)} 成功")
        sys.exit(0 if success_count == len(results) else 1)
    else:
        result = asyncio.run(debug_platform(args.platform, headless=args.headless))
        sys.exit(0 if result["success"] else 1)

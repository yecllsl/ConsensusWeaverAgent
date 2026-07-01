"""ConsensusWeaver MCP Server 入口

通过 MCP 协议暴露 4 个工具：
- ask_ai: 并行向多个 AI WebApp 提问
- list_platforms: 列出支持的 AI 平台
- check_login: 检查/准备登录状态
- capture_screenshot: 截图调试
"""
from typing import List, Optional

from fastmcp import FastMCP

from core.config import Config
from core.platform_manager import PlatformManager
from utils.logger import get_logger

# 初始化 MCP Server
mcp = FastMCP("ConsensusWeaver")

# 加载配置
config = Config.load("config.yaml")
logger = get_logger("mcp_server", config.paths.log_dir)

# 全局平台管理器实例
_manager: Optional[PlatformManager] = None


def get_manager() -> PlatformManager:
    """获取或创建平台管理器单例"""
    global _manager
    if _manager is None:
        _manager = PlatformManager(config)
    return _manager


@mcp.tool()
async def ask_ai(
    question: str,
    platforms: Optional[List[str]] = None,
    timeout: int = 120,
    min_success: int = 3,
) -> dict:
    """向多个 AI WebApp 并行提问，收集答案

    Args:
        question: 要提问的问题内容
        platforms: 指定提问哪些平台（如 ["doubao", "deepseek"]），不传则全部
        timeout: 单个平台的超时时间（秒），默认 120
        min_success: 最少成功数量，低于此数则整体失败，默认 3

    Returns:
        包含各平台答案的汇总结果
    """
    logger.info(f"ask_ai 调用: question={question[:50]}..., platforms={platforms}")

    # 参数校验
    if not question or not question.strip():
        return {"success": False, "error": "问题内容不能为空"}

    if timeout < 1 or timeout > 600:
        return {"success": False, "error": "超时时间应在 1-600 秒之间"}

    if min_success < 1:
        return {"success": False, "error": "最小成功数应大于 0"}

    manager = get_manager()
    result = await manager.ask_question(
        question=question,
        platforms=platforms,
        timeout=timeout,
        min_success=min_success,
    )
    return result


@mcp.tool()
async def list_platforms() -> dict:
    """列出当前所有支持的 AI 平台及其可用状态

    Returns:
        包含平台列表的字典
    """
    logger.info("list_platforms 调用")
    manager = get_manager()
    return await manager.list_platforms()


@mcp.tool()
async def check_login(
    platform: str,
    headless: bool = False,
    wait_login_seconds: int = 0,
) -> dict:
    """检查指定平台的登录状态

    Args:
        platform: 平台 ID（如 "doubao"）
        headless: 是否无头模式，默认 False（便于手动登录）
        wait_login_seconds: 等待手动登录的秒数，>0 时打开浏览器等待，默认 0

    Returns:
        包含登录状态信息的字典
    """
    logger.info(f"check_login 调用: platform={platform}, wait={wait_login_seconds}")

    if not platform or not platform.strip():
        return {"platform": "", "is_logged_in": False, "message": "平台 ID 不能为空"}

    manager = get_manager()

    # 如果需要等待手动登录
    if wait_login_seconds > 0:
        import asyncio
        adapter = await manager._create_adapter(platform)
        await adapter.navigate_to_chat()
        logger.info(f"浏览器已打开，等待 {wait_login_seconds} 秒供用户登录...")
        await asyncio.sleep(wait_login_seconds)

    result = await manager.check_login(platform, headless=headless)
    return result


@mcp.tool()
async def capture_screenshot(platform: str) -> dict:
    """对指定平台的当前页面截图，用于调试

    Args:
        platform: 平台 ID（如 "doubao"）

    Returns:
        包含截图路径和当前页面 URL 的字典
    """
    logger.info(f"capture_screenshot 调用: platform={platform}")

    if not platform or not platform.strip():
        return {"platform": "", "screenshot_path": "", "page_url": "", "error": "平台 ID 不能为空"}

    manager = get_manager()
    return await manager.capture_screenshot(platform)


# 为工具函数附加 .fn 属性（指向函数自身），兼容 FunctionTool 风格的外部调用
# fastmcp 3.x 的 @mcp.tool() 返回原始函数而非 FunctionTool 对象，此处补齐 .fn
ask_ai.fn = ask_ai
list_platforms.fn = list_platforms
check_login.fn = check_login
capture_screenshot.fn = capture_screenshot


if __name__ == "__main__":
    mcp.run()

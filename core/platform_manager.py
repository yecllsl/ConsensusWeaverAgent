"""平台管理器 - 平台注册、并发调度、结果汇总"""
import asyncio
from typing import Dict, List, Optional, Type

from adapters.base_adapter import BaseAdapter, AdapterResult
from adapters.doubao_adapter import DoubaoAdapter
from adapters.chatglm_adapter import ChatGLMAdapter
from adapters.deepseek_adapter import DeepSeekAdapter
from adapters.qianwen_adapter import QianwenAdapter
from adapters.yuanbao_adapter import YuanbaoAdapter
from core.browser_pool import BrowserPool
from core.config import Config
from utils.logger import get_logger


class PlatformManager:
    """平台管理器

    负责平台适配器的注册与发现、并发调度各平台提问、汇总结果。
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger("platform_manager")
        self._browser_pool = BrowserPool(config.browser)

        # 适配器注册表：platform_id -> AdapterClass
        self._adapter_registry: Dict[str, Type[BaseAdapter]] = {
            "doubao": DoubaoAdapter,
            "chatglm": ChatGLMAdapter,
            "deepseek": DeepSeekAdapter,
            "qianwen": QianwenAdapter,
            "yuanbao": YuanbaoAdapter,
        }

    def get_enabled_platforms(self) -> List[str]:
        """获取所有已启用且已注册的平台 ID 列表"""
        enabled_in_config = self.config.get_enabled_platforms()
        return [p for p in enabled_in_config if p in self._adapter_registry]

    async def _create_adapter(self, platform_id: str) -> BaseAdapter:
        """为指定平台创建适配器实例"""
        adapter_class = self._adapter_registry[platform_id]
        page = await self._browser_pool.get_page(platform_id)
        return adapter_class(page=page)

    async def ask_question(
        self,
        question: str,
        platforms: Optional[List[str]] = None,
        timeout: int = 120,
        min_success: int = 3,
    ) -> dict:
        """并行向多个平台提问并汇总结果"""
        if platforms is None:
            target_platforms = self.get_enabled_platforms()
        else:
            target_platforms = [p for p in platforms if p in self._adapter_registry]
            if len(target_platforms) < len(platforms):
                invalid = set(platforms) - set(target_platforms)
                self.logger.warning(f"忽略未注册的平台: {invalid}")

        self.logger.info(f"开始并行提问，目标平台: {target_platforms}")

        tasks = [self._ask_single_platform(pid, question, timeout) for pid in target_platforms]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results: List[AdapterResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                platform_id = target_platforms[i]
                platform_name = self.config.platforms.get(platform_id)
                platform_name = platform_name.name if platform_name else platform_id
                processed_results.append(AdapterResult(
                    platform=platform_id,
                    platform_name=platform_name,
                    status="failed",
                    answer=None,
                    duration_ms=0,
                    screenshot_path=None,
                    error=f"未捕获异常: {str(result)}",
                ))
            else:
                processed_results.append(result)

        success_count = sum(1 for r in processed_results if r.is_success)
        total_count = len(processed_results)
        is_success = success_count >= min_success

        self.logger.info(
            f"提问完成: {success_count}/{total_count} 成功, "
            f"最小要求 {min_success}, 整体{'成功' if is_success else '失败'}"
        )

        return {
            "success": is_success,
            "total_count": total_count,
            "success_count": success_count,
            "question": question,
            "results": [r.to_dict() for r in processed_results],
        }

    async def _ask_single_platform(self, platform_id: str, question: str, timeout: int) -> AdapterResult:
        """向单个平台提问"""
        try:
            adapter = await self._create_adapter(platform_id)
            return await adapter.ask(question, timeout)
        except Exception as e:
            platform_name = self.config.platforms.get(platform_id)
            platform_name = platform_name.name if platform_name else platform_id
            self.logger.error(f"平台 {platform_name} 执行异常: {e}")
            return AdapterResult(
                platform=platform_id,
                platform_name=platform_name,
                status="failed",
                answer=None,
                duration_ms=0,
                screenshot_path=None,
                error=str(e),
            )

    async def check_login(self, platform_id: str, headless: bool = False) -> dict:
        """检查指定平台的登录状态"""
        adapter = await self._create_adapter(platform_id)
        is_logged_in = await adapter.check_login_status()
        platform_name = self.config.platforms.get(platform_id)
        platform_name = platform_name.name if platform_name else platform_id
        return {
            "platform": platform_id,
            "is_logged_in": is_logged_in,
            "message": "登录状态正常" if is_logged_in else f"未登录，请先登录 {platform_name}",
        }

    async def capture_screenshot(self, platform_id: str) -> dict:
        """对指定平台截图"""
        from datetime import datetime
        adapter = await self._create_adapter(platform_id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"{self.config.paths.screenshot_dir}/debug_{platform_id}_{timestamp}.png"
        from pathlib import Path
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        actual_path = await adapter.capture_screenshot(save_path)
        page_url = adapter.page.url
        return {
            "platform": platform_id,
            "screenshot_path": actual_path,
            "page_url": page_url,
        }

    async def list_platforms(self) -> dict:
        """列出所有平台及其状态"""
        platforms_info = []
        for pid, adapter_class in self._adapter_registry.items():
            pconfig = self.config.platforms.get(pid)
            platforms_info.append({
                "id": pid,
                "name": pconfig.name if pconfig else pid,
                "url": pconfig.base_url if pconfig else "",
                "enabled": pconfig.enabled if pconfig else False,
                "login_status": "unknown",
            })
        return {"platforms": platforms_info}

    async def cleanup(self) -> None:
        """清理资源"""
        await self._browser_pool.stop()

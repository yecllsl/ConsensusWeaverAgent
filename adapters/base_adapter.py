"""平台适配器基类，定义统一接口"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils.logger import get_logger


@dataclass
class AdapterResult:
    """适配器执行结果"""
    platform: str
    platform_name: str
    status: str  # "success" 或 "failed"
    answer: Optional[str]
    duration_ms: int
    screenshot_path: Optional[str]
    error: Optional[str]

    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.status == "success"

    def to_dict(self) -> dict:
        """转为字典"""
        return asdict(self)


class BaseAdapter(ABC):
    """平台适配器基类

    所有 AI 平台适配器继承此类，实现统一的接口。
    每个适配器负责一个平台的浏览器自动化操作。
    """

    def __init__(self, platform_id: str, platform_name: str, base_url: str):
        self.platform_id = platform_id
        self.platform_name = platform_name
        self.base_url = base_url
        self.logger = get_logger(f"adapter.{platform_id}")

    @abstractmethod
    async def navigate_to_chat(self) -> None:
        """导航到聊天页面"""
        pass

    @abstractmethod
    async def check_login_status(self) -> bool:
        """检查是否已登录，返回 True/False"""
        pass

    @abstractmethod
    async def send_question(self, question: str) -> None:
        """在输入框中输入问题并发送"""
        pass

    @abstractmethod
    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待回答完成，返回答案文本"""
        pass

    @abstractmethod
    async def capture_screenshot(self, save_path: str) -> str:
        """截取当前页面，返回保存路径"""
        pass

    @abstractmethod
    async def new_chat(self) -> None:
        """开启新对话"""
        pass

    async def ask(self, question: str, timeout: int = 120) -> AdapterResult:
        """完整提问流程封装

        依次执行：导航 → 登录检查 → 新对话 → 发送 → 等待 → 提取 → 截图
        """
        start_time = datetime.now()
        screenshot_path = None
        error_msg = None
        answer = None

        try:
            await self.navigate_to_chat()
            is_logged_in = await self.check_login_status()
            if not is_logged_in:
                raise RuntimeError(f"未登录: 请先调用 check_login 登录 {self.platform_name}")
            await self.new_chat()
            await self.send_question(question)
            answer = await self.wait_for_answer(timeout)
            screenshot_path = await self._save_screenshot()
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"{self.platform_name} 提问失败: {error_msg}")
            try:
                screenshot_path = await self._save_screenshot()
            except Exception:
                pass

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        status = "success" if error_msg is None else "failed"

        return AdapterResult(
            platform=self.platform_id,
            platform_name=self.platform_name,
            status=status,
            answer=answer,
            duration_ms=duration_ms,
            screenshot_path=screenshot_path,
            error=error_msg,
        )

    async def _save_screenshot(self) -> Optional[str]:
        """保存截图，子类可覆盖以指定保存路径"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"./data/screenshots/{self.platform_id}_{timestamp}.png"
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            return await self.capture_screenshot(save_path)
        except Exception:
            return None

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

from src.infrastructure.config.config_manager import RetryConfig
from src.infrastructure.logging.logger import get_logger


@dataclass
class RetryResult:
    success: bool
    attempts: int
    total_time: float
    value: Optional[Any] = None
    error: Optional[str] = None


class RetryHandler:
    def __init__(self, config: RetryConfig):
        self.config = config
        self.current_attempt = 0
        self.logger = get_logger()

    async def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> RetryResult:
        self.current_attempt = 0

        if not self.config.enabled:
            result = await func(*args, **kwargs)
            return RetryResult(
                success=True,
                attempts=1,
                total_time=0.0,
                value=result,
            )

        start_time = time.time()
        last_error = None

        while self.current_attempt < self.config.max_retries:
            self.current_attempt += 1

            try:
                result = await func(*args, **kwargs)
                return RetryResult(
                    success=True,
                    attempts=self.current_attempt,
                    total_time=time.time() - start_time,
                    value=result,
                )
            except asyncio.TimeoutError as e:
                last_error = f"超时错误: {str(e)}"
                self.logger.warning(f"第{self.current_attempt}次尝试超时: {last_error}")
                if not self.config.retry_on_timeout:
                    break
            except Exception as e:
                last_error = f"执行错误: {str(e)}"
                self.logger.warning(f"第{self.current_attempt}次尝试失败: {last_error}")
                if not self.config.retry_on_error:
                    break

            if self.current_attempt >= self.config.max_retries:
                self.logger.error(f"已达到最大重试次数: {self.config.max_retries}")
                break

            if self.config.auto_retry:
                delay = self._calculate_delay()
                self.logger.info(f"等待 {delay} 秒后自动重试...")
                await asyncio.sleep(delay)
            else:
                if not await self._ask_user_retry(last_error):
                    self.logger.info("用户选择放弃重试")
                    break

        return RetryResult(
            success=False,
            attempts=self.current_attempt,
            total_time=time.time() - start_time,
            error=last_error,
        )

    def _calculate_delay(self) -> float:
        if self.config.exponential_backoff:
            return float(self.config.retry_delay * (2 ** (self.current_attempt - 1)))
        return float(self.config.retry_delay)

    async def _ask_user_retry(self, error: str) -> bool:
        print(f"\n调用失败: {error}")
        print(f"已尝试 {self.current_attempt}/{self.config.max_retries} 次")

        while True:
            choice = input("是否重试？: ").strip().lower()
            if choice in ["y", "yes"]:
                self.logger.info("用户选择重试")
                return True
            elif choice in ["n", "no"]:
                self.logger.info("用户选择放弃")
                return False
            print("请输入 y 或 n")

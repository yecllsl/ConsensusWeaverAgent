"""重试处理器

本模块实现了重试机制，用于处理临时性错误和提高系统稳定性。
"""
import asyncio
import logging
import random
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


class RetryHandler:
    """重试处理器
    
    提供指数退避重试机制，用于处理临时性错误。
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.logger = logging.getLogger(__name__)

    def calculate_delay(self, attempt: int) -> float:
        """计算退避延迟（指数退避）"""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt), self.max_delay
        )
        jitter = delay * 0.1 * random.random()
        return delay + jitter

    async def execute_with_retry(
        self, func: Callable[..., T], *args: Any, **kwargs: Any
    ) -> T:
        """执行函数并在失败时重试"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    self.logger.warning(
                        f"操作失败（尝试 {attempt + 1}/{self.max_retries + 1}）：{e}，"
                        f"{delay:.2f}秒后重试..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"操作失败，已达到最大重试次数：{e}"
                    )
                    raise

        raise last_exception

    def retry_decorator(
        self,
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None,
    ):
        """重试装饰器"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                retry_handler = RetryHandler(
                    max_retries=max_retries or self.max_retries,
                    base_delay=base_delay or self.base_delay,
                    max_delay=self.max_delay,
                    exponential_base=self.exponential_base,
                )
                return await retry_handler.execute_with_retry(
                    func, *args, **kwargs
                )

            return wrapper

        return decorator

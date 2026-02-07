"""测试重试处理器"""
import asyncio
import pytest
from unittest.mock import Mock, patch

from src.infrastructure.data.retry_handler import RetryHandler


class TestRetryHandler:
    """测试重试处理器"""

    def test_initialization(self):
        """测试重试处理器初始化"""
        handler = RetryHandler(
            max_retries=3,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
        )

        assert handler.max_retries == 3
        assert handler.base_delay == 1.0
        assert handler.max_delay == 60.0
        assert handler.exponential_base == 2.0

    def test_calculate_delay(self):
        """测试计算退避延迟"""
        handler = RetryHandler(
            max_retries=3,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
        )

        delay = handler.calculate_delay(0)
        assert delay >= 1.0
        assert delay <= 1.1

        delay = handler.calculate_delay(1)
        assert delay >= 2.0
        assert delay <= 2.2

        delay = handler.calculate_delay(10)
        assert delay <= 60.0

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """测试成功执行"""
        handler = RetryHandler(max_retries=3, base_delay=0.1)

        async def success_func():
            return "success"

        result = await handler.execute_with_retry(success_func)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_failure_then_success(self):
        """测试失败后重试成功"""
        handler = RetryHandler(max_retries=3, base_delay=0.1)
        attempt_count = 0

        async def flaky_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ValueError("临时错误")
            return "success"

        result = await handler.execute_with_retry(flaky_func)

        assert result == "success"
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        handler = RetryHandler(max_retries=2, base_delay=0.1)

        async def failing_func():
            raise ValueError("持续错误")

        with pytest.raises(ValueError, match="持续错误"):
            await handler.execute_with_retry(failing_func)

    @pytest.mark.asyncio
    async def test_execute_with_retry_sync_function(self):
        """测试同步函数"""
        handler = RetryHandler(max_retries=3, base_delay=0.1)

        def sync_func():
            return "sync_result"

        result = await handler.execute_with_retry(sync_func)

        assert result == "sync_result"

    def test_retry_decorator(self):
        """测试重试装饰器"""
        handler = RetryHandler(max_retries=3, base_delay=0.1)

        @handler.retry_decorator()
        async def decorated_func():
            return "decorated"

        assert asyncio.iscoroutinefunction(decorated_func)

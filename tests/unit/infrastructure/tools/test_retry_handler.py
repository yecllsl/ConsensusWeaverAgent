import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.infrastructure.tools.retry_handler import (
    RetryConfig,
    RetryHandler,
)


@pytest.fixture
def retry_config():
    """创建重试配置"""
    return RetryConfig(
        enabled=True,
        auto_retry=True,
        max_retries=3,
        retry_delay=1,
        retry_on_timeout=True,
        retry_on_error=True,
        exponential_backoff=False,
    )


@pytest.fixture
def retry_handler(retry_config):
    """创建重试处理器实例"""
    return RetryHandler(retry_config)


class TestRetryHandler:
    """测试重试处理器"""

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, retry_handler):
        """测试执行成功（无需重试）"""
        async_func = AsyncMock(return_value="success")

        result = await retry_handler.execute_with_retry(async_func)

        assert result.success
        assert result.value == "success"
        assert result.attempts == 1
        assert async_func.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_disabled(self, retry_config):
        """测试重试禁用"""
        retry_config.enabled = False
        handler = RetryHandler(retry_config)

        async_func = AsyncMock(return_value="success")

        result = await handler.execute_with_retry(async_func)

        assert result.success
        assert result.value == "success"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_timeout(self, retry_handler):
        """测试超时重试"""
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise asyncio.TimeoutError("Timeout")
            return "success"

        result = await retry_handler.execute_with_retry(failing_func)

        assert result.success
        assert result.value == "success"
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_error(self, retry_handler):
        """测试错误重试"""
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Error")
            return "success"

        result = await retry_handler.execute_with_retry(failing_func)

        assert result.success
        assert result.value == "success"
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries_exceeded(self, retry_handler):
        """测试超过最大重试次数"""
        async_func = AsyncMock(side_effect=ValueError("Error"))

        result = await retry_handler.execute_with_retry(async_func)

        assert not result.success
        assert result.error == "执行错误: Error"
        assert result.attempts == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_no_retry_on_timeout(self, retry_config):
        """测试不重试超时"""
        retry_config.retry_on_timeout = False
        handler = RetryHandler(retry_config)

        async_func = AsyncMock(side_effect=asyncio.TimeoutError("Timeout"))

        result = await handler.execute_with_retry(async_func)

        assert not result.success
        assert result.error == "超时错误: Timeout"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_no_retry_on_error(self, retry_config):
        """测试不重试错误"""
        retry_config.retry_on_error = False
        handler = RetryHandler(retry_config)

        async_func = AsyncMock(side_effect=ValueError("Error"))

        result = await handler.execute_with_retry(async_func)

        assert not result.success
        assert result.error == "执行错误: Error"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_exponential_backoff(self, retry_config):
        """测试指数退避"""
        retry_config.exponential_backoff = True
        retry_config.retry_delay = 1
        handler = RetryHandler(retry_config)

        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Error")
            return "success"

        import time

        start_time = time.time()
        result = await handler.execute_with_retry(failing_func)
        elapsed_time = time.time() - start_time

        assert result.success
        assert result.attempts == 3
        assert elapsed_time >= 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_interactive_retry(self, retry_config, capsys):
        """测试交互式重试"""
        retry_config.auto_retry = False
        handler = RetryHandler(retry_config)

        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Error")
            return "success"

        with patch("builtins.input", return_value="y"):
            result = await handler.execute_with_retry(failing_func)

        assert result.success
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_interactive_abort(self, retry_config, capsys):
        """测试交互式重试（放弃）"""
        retry_config.auto_retry = False
        handler = RetryHandler(retry_config)

        async_func = AsyncMock(side_effect=ValueError("Error"))

        with patch("builtins.input", return_value="n"):
            result = await handler.execute_with_retry(async_func)

        assert not result.success
        assert result.attempts == 1

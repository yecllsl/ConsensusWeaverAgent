#!/usr/bin/env python3
"""
ToolManager 单元测试
"""

import asyncio
import subprocess

# 添加项目根目录到Python路径
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.config.config_manager import ConfigManager, ExternalToolConfig
from src.infrastructure.tools.tool_manager import ToolManager


@dataclass
class MockConfig:
    """模拟配置对象"""

    class NetworkConfig:
        timeout: int = 120

    class AppConfig:
        max_parallel_tools: int = 5

    external_tools: List[ExternalToolConfig]
    network: NetworkConfig = NetworkConfig()
    app: AppConfig = AppConfig()


@pytest.fixture
def mock_config_manager():
    """创建模拟配置管理器"""
    # 创建模拟配置
    config = MockConfig(
        external_tools=[
            ExternalToolConfig(
                name="iflow",
                command="iflow",
                args="-y -p",
                needs_internet=True,
                priority=1,
                enabled=True,
            ),
            ExternalToolConfig(
                name="codebuddy",
                command="codebuddy",
                args="-p",
                needs_internet=True,
                priority=2,
                enabled=True,
            ),
        ]
    )

    # 创建模拟配置管理器
    config_manager = MagicMock(spec=ConfigManager)
    config_manager.get_config.return_value = config

    return config_manager


@pytest.fixture
def tool_manager(mock_config_manager):
    """创建ToolManager实例"""
    return ToolManager(mock_config_manager)


@pytest.mark.asyncio
async def test_run_tool_not_found(tool_manager):
    """测试工具未找到"""
    # 调用不存在的工具
    result = await tool_manager.run_tool("nonexistent", "测试问题")

    # 验证结果
    assert result.success is False
    assert "工具 nonexistent 未找到" in result.error_message


@pytest.mark.asyncio
async def test_run_tool_timeout(tool_manager):
    """测试工具调用超时"""
    # 模拟超时
    with patch("asyncio.create_subprocess_exec") as mock_create_subprocess:
        # 创建一个模拟的进程对象
        mock_process = MagicMock()
        # 让communicate方法抛出超时异常
        mock_process.communicate = MagicMock(side_effect=asyncio.TimeoutError())
        # 让create_subprocess_exec返回模拟进程
        mock_create_subprocess.return_value = mock_process

        # 调用工具
        result = await tool_manager.run_tool("iflow", "测试问题")

        # 验证结果
        assert result.success is False
        assert "执行超时" in result.error_message


@pytest.mark.asyncio
async def test_run_tool_exception(tool_manager):
    """测试工具调用抛出异常"""
    # 模拟异常
    with patch("asyncio.create_subprocess_exec") as mock_create_subprocess:
        # 让create_subprocess_exec直接抛出异常
        mock_create_subprocess.side_effect = Exception("模拟异常")

        # 调用工具
        result = await tool_manager.run_tool("iflow", "测试问题")

        # 验证结果
        assert result.success is False
        assert "模拟异常" in result.error_message


@pytest.fixture
def mock_process():
    """创建模拟的进程对象"""
    mock_process = MagicMock()

    # 让communicate返回协程对象
    async def mock_communicate():
        return (b"", b"")

    mock_process.communicate = mock_communicate
    mock_process.returncode = 0
    return mock_process


@pytest.mark.asyncio
async def test_run_tool_success(tool_manager, mock_process):
    """测试工具调用成功"""

    # 定义新的communicate函数，返回指定的内容
    async def mock_communicate_success():
        return (b"This is the tool's answer", b"")

    # 替换communicate函数
    mock_process.communicate = mock_communicate_success
    mock_process.returncode = 0

    # 模拟成功的命令执行
    with patch("asyncio.create_subprocess_exec") as mock_create_subprocess:
        # 让create_subprocess_exec返回模拟进程
        mock_create_subprocess.return_value = mock_process

        # 调用工具
        result = await tool_manager.run_tool("iflow", "测试问题")

        # 验证结果
        assert result.success is True
        assert result.answer == "This is the tool's answer"
        assert result.error_message == ""
        assert result.tool_name == "iflow"


@pytest.mark.asyncio
async def test_run_tool_failure(tool_manager, mock_process):
    """测试工具调用失败"""

    # 定义新的communicate函数，返回失败内容
    async def mock_communicate_failure():
        return (b"", b"Tool execution failed")

    # 替换communicate函数
    mock_process.communicate = mock_communicate_failure
    mock_process.returncode = 1

    # 模拟失败的命令执行
    with patch("asyncio.create_subprocess_exec") as mock_create_subprocess:
        # 让create_subprocess_exec返回模拟进程
        mock_create_subprocess.return_value = mock_process

        # 调用工具
        result = await tool_manager.run_tool("iflow", "测试问题")

        # 验证结果
        assert result.success is False
        assert result.answer == ""
        assert "返回码: 1" in result.error_message
        assert "Tool execution failed" in result.error_message
        assert result.tool_name == "iflow"


@pytest.mark.asyncio
async def test_command_construction(tool_manager, mock_process):
    """测试命令参数构建是否正确"""
    # 设置模拟返回值
    mock_process.communicate.return_value = (b"", b"")
    mock_process.returncode = 0

    # 模拟成功的命令执行
    with patch("asyncio.create_subprocess_exec") as mock_create_subprocess:
        # 让create_subprocess_exec返回模拟进程
        mock_create_subprocess.return_value = mock_process

        # 调用工具
        await tool_manager.run_tool("iflow", "测试问题")

        # 验证命令构建
        mock_create_subprocess.assert_called_once()
        args, kwargs = mock_create_subprocess.call_args

        # 验证命令参数
        assert args[0] == "iflow"
        assert args[1] == "-y"
        assert args[2] == "-p"
        assert args[3] == "测试问题"

        # 验证stdout和stderr都设置为PIPE
        assert kwargs["stdout"] == subprocess.PIPE
        assert kwargs["stderr"] == subprocess.PIPE

        # 验证没有设置text=True参数
        assert "text" not in kwargs


@pytest.mark.asyncio
async def test_output_decoding(tool_manager, mock_process):
    """测试输出解码是否正确"""

    # 定义新的communicate函数，返回包含非ASCII字符的内容
    async def mock_communicate_non_ascii():
        return (
            b"This is the tool's answer with non-ASCII: \xc3\xa9",  # 包含法语字符é
            b"Error message: \xc3\xa0",
        )

    # 替换communicate函数
    mock_process.communicate = mock_communicate_non_ascii
    mock_process.returncode = 0

    # 模拟命令执行
    with patch("asyncio.create_subprocess_exec") as mock_create_subprocess:
        # 让create_subprocess_exec返回模拟进程
        mock_create_subprocess.return_value = mock_process

        # 调用工具
        result = await tool_manager.run_tool("iflow", "测试问题")

        # 验证输出被正确解码
        assert result.success is True
        assert "non-ASCII: é" in result.answer


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v"])

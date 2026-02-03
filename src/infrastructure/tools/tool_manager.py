import asyncio
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.logging.logger import get_logger
from src.infrastructure.tools.retry_handler import RetryHandler
from src.infrastructure.tools.tool_selector import ToolSelector


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    answer: str
    error_message: str
    execution_time: float
    timestamp: str


class ToolManager:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.get_config()
        self.logger = get_logger()
        self.enabled_tools = [
            tool for tool in self.config.external_tools if tool.enabled
        ]
        self.enabled_tools.sort(key=lambda x: x.priority)
        self.retry_handler = RetryHandler(self.config.retry)
        self.tool_selector = ToolSelector(config_manager)
        self.logger.info(f"已加载 {len(self.enabled_tools)} 个外部工具")

    async def run_tool(self, tool_name: str, question: str) -> ToolResult:
        """运行单个外部工具"""
        tool_config = next(
            (tool for tool in self.enabled_tools if tool.name == tool_name), None
        )
        if not tool_config:
            self.logger.error(f"工具 {tool_name} 未找到或未启用")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                answer="",
                error_message=f"工具 {tool_name} 未找到或未启用",
                execution_time=0.0,
                timestamp=datetime.now().isoformat(),
            )

        retry_result = await self.retry_handler.execute_with_retry(
            self._execute_tool_internal,
            tool_config,
            question,
        )

        if retry_result.success:
            if retry_result.value is None:
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    answer="",
                    error_message="执行结果为空",
                    execution_time=retry_result.total_time,
                    timestamp=datetime.now().isoformat(),
                )
            result = cast(ToolResult, retry_result.value)
            self.tool_selector.record_tool_execution(
                tool_name=tool_name,
                success=result.success,
                execution_time=result.execution_time,
            )
            return result
        else:
            self.tool_selector.record_tool_execution(
                tool_name=tool_name,
                success=False,
                execution_time=retry_result.total_time,
            )
            return ToolResult(
                tool_name=tool_name,
                success=False,
                answer="",
                error_message=retry_result.error or "执行失败",
                execution_time=retry_result.total_time,
                timestamp=datetime.now().isoformat(),
            )

    async def _execute_tool_internal(
        self, tool_config: Any, question: str
    ) -> ToolResult:
        """内部执行工具方法（不带重试）"""
        import time
        from datetime import datetime

        tool_name = tool_config.name
        start_time = time.time()
        timestamp = datetime.now().isoformat()

        try:
            # 安全地构建命令参数列表
            import shlex

            # 解析工具命令和参数
            full_command = f"{tool_config.command} {tool_config.args}"
            base_args = shlex.split(full_command)
            # 添加问题作为最后一个参数
            command_args = base_args + [question]

            # 检查是否为PowerShell脚本
            is_powershell_script = False
            if sys.platform == "win32" and tool_config.command.endswith(".ps1"):
                is_powershell_script = True

            # 对于PowerShell脚本，需要通过powershell.exe执行
            if is_powershell_script:
                # 构建PowerShell命令
                full_script_command = " ".join(shlex.quote(arg) for arg in command_args)
                power_args = [
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    full_script_command,
                ]
                process_command = "powershell.exe"
                process_args = power_args
                self.logger.info(
                    f"运行PowerShell脚本: {process_command} {' '.join(process_args)}"
                )
            else:
                # 对于普通可执行文件，直接运行
                process_command = command_args[0]
                process_args = command_args[1:]
                # 记录运行的外部工具和参数
                quoted_args = " ".join(shlex.quote(arg) for arg in process_args)
                self.logger.info(f"运行外部工具: {process_command} {quoted_args}")

            # 运行命令（不使用shell=True，更安全）
            process = await asyncio.create_subprocess_exec(
                process_command,
                *process_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                # 不使用text=True，避免兼容性问题
            )

            # 等待命令完成，设置超时
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=self.config.network.timeout
            )

            # 手动解码输出
            stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr = stderr_bytes.decode("utf-8", errors="replace").strip()

            execution_time = time.time() - start_time

            if process.returncode == 0:
                self.logger.info(
                    f"工具 {tool_name} 执行成功，耗时 {execution_time:.2f} 秒"
                )
                return ToolResult(
                    tool_name=tool_name,
                    success=True,
                    answer=stdout.strip(),
                    error_message="",
                    execution_time=execution_time,
                    timestamp=timestamp,
                )
            else:
                self.logger.error(
                    f"工具 {tool_name} 执行失败，返回码: {process.returncode}"
                )
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    answer="",
                    error_message=(
                        f"返回码: {process.returncode}, 错误信息: {stderr.strip()}"
                    ),
                    execution_time=execution_time,
                    timestamp=timestamp,
                )

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            self.logger.error(
                f"工具 {tool_name} 执行超时 ({self.config.network.timeout} 秒)"
            )
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"工具 {tool_name} 执行异常: {e}")
            raise

    async def run_multiple_tools(
        self, question: str, tool_names: Optional[List[str]] = None
    ) -> List[ToolResult]:
        """运行多个外部工具"""
        if not tool_names:
            tool_names = [tool.name for tool in self.enabled_tools]

        # 限制并发工具数量
        max_parallel = self.config.app.max_parallel_tools
        tool_names = tool_names[:max_parallel]

        self.logger.info(f"并行运行 {len(tool_names)} 个外部工具")

        # 创建任务
        tasks = [self.run_tool(tool_name, question) for tool_name in tool_names]

        # 等待所有任务完成
        results = await asyncio.gather(*tasks)

        return results

    def get_enabled_tools(self) -> List[Dict[str, Any]]:
        """获取所有启用的工具"""
        return [
            {
                "name": tool.name,
                "command": tool.command,
                "args": tool.args,
                "needs_internet": tool.needs_internet,
                "priority": tool.priority,
            }
            for tool in self.enabled_tools
        ]

    def check_internet_connection(self) -> bool:
        """检查网络连接"""
        try:
            import socket

            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except (socket.error, TimeoutError):
            return False

    def update_config(self, config_manager: ConfigManager) -> None:
        """更新工具配置"""
        self.config = config_manager.get_config()
        self.enabled_tools = [
            tool for tool in self.config.external_tools if tool.enabled
        ]
        self.enabled_tools.sort(key=lambda x: x.priority)
        self.retry_handler = RetryHandler(self.config.retry)
        self.tool_selector = ToolSelector(config_manager)
        self.logger.info(
            f"已更新工具配置，当前启用 {len(self.enabled_tools)} 个外部工具"
        )

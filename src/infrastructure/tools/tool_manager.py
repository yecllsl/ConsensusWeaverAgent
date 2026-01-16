import asyncio
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.logging.logger import get_logger


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
        self.enabled_tools = [tool for tool in self.config.external_tools if tool.enabled]
        self.enabled_tools.sort(key=lambda x: x.priority)
        self.logger.info(f"已加载 {len(self.enabled_tools)} 个外部工具")

    async def run_tool(self, tool_name: str, question: str) -> ToolResult:
        """运行单个外部工具"""
        import time
        from datetime import datetime
        
        tool_config = next((tool for tool in self.enabled_tools if tool.name == tool_name), None)
        if not tool_config:
            self.logger.error(f"工具 {tool_name} 未找到或未启用")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                answer="",
                error_message=f"工具 {tool_name} 未找到或未启用",
                execution_time=0.0,
                timestamp=datetime.now().isoformat()
            )
        
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            # 构建命令
            command = f"{tool_config.command} {tool_config.args} \"{question}\""
            
            self.logger.info(f"运行外部工具: {command}")
            
            # 运行命令
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待命令完成，设置超时
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.network.timeout
            )
            
            execution_time = time.time() - start_time
            
            if process.returncode == 0:
                self.logger.info(f"工具 {tool_name} 执行成功，耗时 {execution_time:.2f} 秒")
                return ToolResult(
                    tool_name=tool_name,
                    success=True,
                    answer=stdout.strip(),
                    error_message="",
                    execution_time=execution_time,
                    timestamp=timestamp
                )
            else:
                self.logger.error(f"工具 {tool_name} 执行失败，返回码: {process.returncode}")
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    answer="",
                    error_message=f"返回码: {process.returncode}, 错误信息: {stderr.strip()}",
                    execution_time=execution_time,
                    timestamp=timestamp
                )
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            self.logger.error(f"工具 {tool_name} 执行超时 ({self.config.network.timeout} 秒)")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                answer="",
                error_message=f"执行超时 ({self.config.network.timeout} 秒)",
                execution_time=execution_time,
                timestamp=timestamp
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"工具 {tool_name} 执行异常: {e}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                answer="",
                error_message=str(e),
                execution_time=execution_time,
                timestamp=timestamp
            )

    async def run_multiple_tools(self, question: str, tool_names: Optional[List[str]] = None) -> List[ToolResult]:
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
                "priority": tool.priority
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
        self.enabled_tools = [tool for tool in self.config.external_tools if tool.enabled]
        self.enabled_tools.sort(key=lambda x: x.priority)
        self.logger.info(f"已更新工具配置，当前启用 {len(self.enabled_tools)} 个外部工具")

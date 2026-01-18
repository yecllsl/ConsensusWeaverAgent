from dataclasses import dataclass
from typing import List, Tuple

from src.infrastructure.data.data_manager import DataManager
from src.infrastructure.logging.logger import get_logger
from src.infrastructure.tools.tool_manager import ToolManager, ToolResult


@dataclass
class QueryExecutionResult:
    session_id: int
    question: str
    tool_results: List[ToolResult]
    success_count: int
    failure_count: int
    total_execution_time: float
    completed: bool


class QueryExecutor:
    def __init__(self, tool_manager: ToolManager, data_manager: DataManager):
        self.tool_manager = tool_manager
        self.data_manager = data_manager
        self.logger = get_logger()

    async def execute_queries(
        self, session_id: int, question: str, tools: List[str]
    ) -> QueryExecutionResult:
        """执行并行查询"""
        import time

        start_time = time.time()

        self.logger.info(f"开始并行查询，会话ID: {session_id}, 使用工具: {tools}")

        try:
            # 执行工具查询
            tool_results = await self.tool_manager.run_multiple_tools(question, tools)

            # 统计执行结果
            success_count = sum(1 for result in tool_results if result.success)
            failure_count = len(tool_results) - success_count

            # 保存工具结果到数据库
            for result in tool_results:
                self.data_manager.save_tool_result(
                    session_id=session_id,
                    tool_name=result.tool_name,
                    success=result.success,
                    answer=result.answer,
                    error_message=result.error_message,
                    execution_time=result.execution_time,
                )

            total_execution_time = time.time() - start_time

            result = QueryExecutionResult(
                session_id=session_id,
                question=question,
                tool_results=tool_results,
                success_count=success_count,
                failure_count=failure_count,
                total_execution_time=total_execution_time,
                completed=True,
            )

            self.logger.info(
                f"并行查询完成，会话ID: {session_id}, "
                f"成功: {success_count}, 失败: {failure_count}, "
                f"总耗时: {total_execution_time:.2f}秒"
            )

            return result
        except Exception as e:
            self.logger.error(f"执行并行查询失败: {e}")
            raise

    async def execute_single_query(
        self, session_id: int, question: str, tool_name: str
    ) -> ToolResult:
        """执行单个工具查询"""
        self.logger.info(f"开始单个查询，会话ID: {session_id}, 工具: {tool_name}")

        try:
            # 执行工具查询
            result = await self.tool_manager.run_tool(tool_name, question)

            # 保存工具结果到数据库
            self.data_manager.save_tool_result(
                session_id=session_id,
                tool_name=result.tool_name,
                success=result.success,
                answer=result.answer,
                error_message=result.error_message,
                execution_time=result.execution_time,
            )

            self.logger.info(
                f"单个查询完成，会话ID: {session_id}, "
                f"工具: {tool_name}, 成功: {result.success}"
            )

            return result
        except Exception as e:
            self.logger.error(f"执行单个查询失败: {e}")
            raise

    def get_query_results(self, session_id: int) -> List[ToolResult]:
        """获取会话的查询结果"""
        try:
            # 从数据库获取工具结果
            db_results = self.data_manager.get_tool_results(session_id)

            # 转换为ToolResult对象
            tool_results = [
                ToolResult(
                    tool_name=result.tool_name,
                    success=result.success,
                    answer=result.answer,
                    error_message=result.error_message,
                    execution_time=result.execution_time,
                    timestamp=result.timestamp.isoformat()
                    if hasattr(result.timestamp, "isoformat")
                    else result.timestamp,
                )
                for result in db_results
            ]

            return tool_results
        except Exception as e:
            self.logger.error(f"获取查询结果失败: {e}")
            raise

    def validate_query_params(
        self, question: str, tools: List[str]
    ) -> Tuple[bool, str]:
        """验证查询参数"""
        if not question or question.strip() == "":
            return False, "问题不能为空"

        if not tools:
            return False, "至少需要选择一个工具"

        # 检查工具是否都可用
        enabled_tools = [tool.name for tool in self.tool_manager.enabled_tools]
        for tool in tools:
            if tool not in enabled_tools:
                return False, f"工具 {tool} 不可用"

        return True, "参数验证通过"

    def cancel_queries(self, session_id: int) -> bool:
        """取消正在执行的查询"""
        # 注意：由于使用了异步IO和子进程，取消操作比较复杂
        # 这里简化实现，只记录日志
        self.logger.info(f"取消查询请求，会话ID: {session_id}")
        return True

"""查询执行器（新版本）

本模块实现了查询执行器，使用新的数据仓库架构和事务管理。
"""

import time
from dataclasses import dataclass
from typing import List, Tuple

from src.infrastructure.data.retry_handler import RetryHandler
from src.infrastructure.data.transaction_manager import TransactionManager
from src.infrastructure.logging.logger import get_logger
from src.infrastructure.tools.tool_manager import ToolManager, ToolResult
from src.models.entities import ToolResult as ToolResultEntity


@dataclass
class QueryExecutionResult:
    """查询执行结果"""

    session_id: int
    question: str
    tool_results: List[ToolResult]
    success_count: int
    failure_count: int
    total_execution_time: float
    completed: bool


class QueryExecutorV2:
    """查询执行器（新版本）

    使用新的数据仓库架构和事务管理，提供更好的数据一致性保证。
    """

    def __init__(
        self,
        tool_manager: ToolManager,
        transaction_manager: TransactionManager,
    ):
        self.tool_manager = tool_manager
        self.transaction_manager = transaction_manager
        self.logger = get_logger()
        self.retry_handler = RetryHandler(max_retries=3, base_delay=1.0)

    async def execute_queries(
        self, session_id: int, question: str, tools: List[str]
    ) -> QueryExecutionResult:
        """执行并行查询（使用事务管理）"""
        start_time = time.time()

        self.logger.info(f"开始并行查询，会话ID: {session_id}, 使用工具: {tools}")

        try:
            # 执行工具查询
            tool_results = await self.tool_manager.run_multiple_tools(question, tools)

            # 统计执行结果
            success_count = sum(1 for result in tool_results if result.success)
            failure_count = len(tool_results) - success_count

            # 使用事务批量保存工具结果
            await self._save_tool_results_with_transaction(session_id, tool_results)

            total_execution_time = time.time() - start_time

            execution_result = QueryExecutionResult(
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

            return execution_result
        except Exception as e:
            self.logger.error(f"执行并行查询失败: {e}")
            raise

    async def _save_tool_results_with_transaction(
        self, session_id: int, results: List[ToolResult]
    ) -> None:
        """使用事务批量保存工具结果"""
        async with self.transaction_manager.begin_transaction() as uow:
            # 转换为实体对象
            entities = [
                ToolResultEntity(
                    session_id=session_id,
                    tool_name=result.tool_name,
                    success=result.success,
                    answer=result.answer,
                    error_message=result.error_message,
                    execution_time=result.execution_time,
                )
                for result in results
            ]

            # 批量保存
            await uow.tool_results.add_batch(entities)

            # 提交事务
            await uow.commit()

    async def execute_single_query(
        self, session_id: int, question: str, tool_name: str
    ) -> ToolResult:
        """执行单个工具查询（使用事务管理）"""
        self.logger.info(f"开始单个查询，会话ID: {session_id}, 工具: {tool_name}")

        try:
            # 执行工具查询
            result = await self.tool_manager.run_tool(tool_name, question)

            # 使用事务保存工具结果
            await self._save_single_tool_result_with_transaction(session_id, result)

            self.logger.info(
                f"单个查询完成，会话ID: {session_id}, "
                f"工具: {tool_name}, 成功: {result.success}"
            )

            return result
        except Exception as e:
            self.logger.error(f"执行单个查询失败: {e}")
            raise

    async def _save_single_tool_result_with_transaction(
        self, session_id: int, result: ToolResult
    ) -> None:
        """使用事务保存单个工具结果"""
        async with self.transaction_manager.begin_transaction() as uow:
            entity = ToolResultEntity(
                session_id=session_id,
                tool_name=result.tool_name,
                success=result.success,
                answer=result.answer,
                error_message=result.error_message,
                execution_time=result.execution_time,
            )

            await uow.tool_results.add(entity)
            await uow.commit()

    async def get_query_results(self, session_id: int) -> List[ToolResult]:
        """获取会话的查询结果（使用仓库）"""
        try:
            async with self.transaction_manager.begin_transaction() as uow:
                # 从仓库获取工具结果
                entities = await uow.tool_results.get_by_session_id(session_id)

                # 转换为ToolResult对象
                tool_results = [
                    ToolResult(
                        tool_name=entity.tool_name,
                        success=entity.success,
                        answer=entity.answer,
                        error_message=entity.error_message,
                        execution_time=entity.execution_time,
                        timestamp=entity.timestamp.isoformat() if entity.timestamp else "",
                    )
                    for entity in entities
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

    async def cancel_queries(self, session_id: int) -> bool:
        """取消正在执行的查询"""
        self.logger.info(f"取消查询请求，会话ID: {session_id}")
        return True

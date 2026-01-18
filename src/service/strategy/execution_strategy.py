from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.infrastructure.llm.llm_service import LLMService
from src.infrastructure.logging.logger import get_logger
from src.infrastructure.tools.tool_manager import ToolManager


@dataclass
class ExecutionPlan:
    strategy: str  # "direct_answer" 或 "parallel_query"
    question: str
    tools: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        pass


class ExecutionStrategyManager:
    def __init__(self, llm_service: LLMService, tool_manager: ToolManager):
        self.llm_service = llm_service
        self.tool_manager = tool_manager
        self.logger = get_logger()

    def create_execution_plan(self, question: str) -> ExecutionPlan:
        """创建执行计划"""
        try:
            # 判断问题复杂度
            complexity = self.llm_service.classify_question_complexity(question)

            self.logger.info(f"问题复杂度判断结果: {complexity}")

            if complexity == "simple":
                # 简单问题，直接回答
                return ExecutionPlan(strategy="direct_answer", question=question)
            else:
                # 复杂问题，并行查询
                tools = self._select_tools(question)
                return ExecutionPlan(
                    strategy="parallel_query", question=question, tools=tools
                )
        except Exception as e:
            self.logger.error(f"创建执行计划失败: {e}")
            raise

    def _select_tools(self, question: str) -> List[str]:
        """选择适合的外部工具"""
        try:
            # 获取所有启用的工具
            enabled_tools = [tool.name for tool in self.tool_manager.enabled_tools]

            # 简单策略：使用所有启用的工具
            # 在实际应用中，可以根据问题类型和工具能力进行更智能的选择
            self.logger.info(f"为问题选择工具: {enabled_tools}")

            return enabled_tools
        except Exception as e:
            self.logger.error(f"选择工具失败: {e}")
            raise

    def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """执行计划"""
        try:
            if plan.strategy == "direct_answer":
                # 直接回答
                answer = self.llm_service.answer_simple_question(plan.question)
                return {
                    "strategy": "direct_answer",
                    "success": True,
                    "answer": answer,
                    "tools": [],
                }
            else:
                # 并行查询
                self.logger.info(f"执行并行查询策略，使用工具: {plan.tools}")
                return {
                    "strategy": "parallel_query",
                    "success": True,
                    "question": plan.question,
                    "tools": plan.tools,
                }
        except Exception as e:
            self.logger.error(f"执行计划失败: {e}")
            raise

    def validate_plan(self, plan: ExecutionPlan) -> bool:
        """验证执行计划"""
        try:
            if plan.strategy == "direct_answer":
                # 直接回答策略始终有效
                return True
            else:
                # 验证并行查询策略
                if not plan.tools:
                    self.logger.error("并行查询策略需要至少一个工具")
                    return False

                # 检查工具是否都可用
                enabled_tools = [tool.name for tool in self.tool_manager.enabled_tools]
                for tool in plan.tools:
                    if tool not in enabled_tools:
                        self.logger.error(f"工具 {tool} 不可用")
                        return False

                # 检查网络连接（如果需要）
                if self.tool_manager.config.network.check_before_run:
                    has_internet = self.tool_manager.check_internet_connection()
                    if not has_internet:
                        self.logger.error("网络连接不可用")
                        return False

                return True
        except Exception as e:
            self.logger.error(f"验证执行计划失败: {e}")
            raise

    def adjust_plan(
        self, plan: ExecutionPlan, feedback: Dict[str, Any]
    ) -> ExecutionPlan:
        """根据反馈调整执行计划"""
        try:
            # 简单实现：如果直接回答策略失败，切换到并行查询策略
            if plan.strategy == "direct_answer" and not feedback.get("success", False):
                self.logger.info("直接回答策略失败，切换到并行查询策略")
                tools = self._select_tools(plan.question)
                return ExecutionPlan(
                    strategy="parallel_query", question=plan.question, tools=tools
                )

            # 如果并行查询策略失败，尝试减少工具数量
            elif plan.strategy == "parallel_query" and not feedback.get(
                "success", False
            ):
                if len(plan.tools) > 1:
                    self.logger.info(
                        f"并行查询策略失败，减少工具数量从 {len(plan.tools)} 到 {len(plan.tools) - 1}"
                    )
                    return ExecutionPlan(
                        strategy="parallel_query",
                        question=plan.question,
                        tools=plan.tools[:-1],
                    )
                else:
                    self.logger.info("并行查询策略失败，切换到直接回答策略")
                    return ExecutionPlan(
                        strategy="direct_answer", question=plan.question
                    )

            # 计划无需调整
            return plan
        except Exception as e:
            self.logger.error(f"调整执行计划失败: {e}")
            raise

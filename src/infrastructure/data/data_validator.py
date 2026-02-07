"""数据验证器

本模块实现了数据验证逻辑，确保数据完整性和一致性。
"""
from typing import List

from src.models.entities import AnalysisResult, Session, ToolResult


class DataValidator:
    """数据验证器
    
    提供数据验证功能，确保数据符合业务规则。
    """

    def validate_session(self, session: Session) -> None:
        """验证会话数据"""
        if not session.original_question or not session.original_question.strip():
            raise ValueError("原始问题不能为空")

        if len(session.original_question) > 1000:
            raise ValueError("问题的长度不能超过1000个字符")

    def validate_tool_result(self, result: ToolResult) -> None:
        """验证工具结果数据"""
        if not result.tool_name or not result.tool_name.strip():
            raise ValueError("工具名称不能为空")

        if result.session_id <= 0:
            raise ValueError("会话ID必须大于0")

        if result.execution_time < 0:
            raise ValueError("执行时间不能为负数")

        if result.success and not result.answer:
            raise ValueError("成功的工具结果必须包含答案")

        if not result.success and not result.error_message:
            raise ValueError("失败的工具结果必须包含错误信息")

    def validate_analysis_result(self, result: AnalysisResult) -> None:
        """验证分析结果数据"""
        if result.session_id <= 0:
            raise ValueError("会话ID必须大于0")

        if not result.similarity_matrix:
            raise ValueError("相似度矩阵不能为空")

        if not result.comprehensive_summary:
            raise ValueError("综合总结不能为空")

        if not result.final_conclusion:
            raise ValueError("最终结论不能为空")

    def validate_batch_sessions(self, sessions: List[Session]) -> None:
        """验证批量会话数据"""
        if not sessions:
            raise ValueError("会话列表不能为空")

        for session in sessions:
            self.validate_session(session)

    def validate_batch_tool_results(self, results: List[ToolResult]) -> None:
        """验证批量工具结果数据"""
        if not results:
            raise ValueError("工具结果列表不能为空")

        for result in results:
            self.validate_tool_result(result)

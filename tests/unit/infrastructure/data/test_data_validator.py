"""测试数据验证器"""

from datetime import datetime

import pytest

from src.infrastructure.data.data_validator import DataValidator
from src.models.entities import AnalysisResult, Session, ToolResult


@pytest.fixture
def data_validator():
    """数据验证器"""
    return DataValidator()


class TestDataValidator:
    """测试数据验证器类"""

    def test_validate_session_valid(self, data_validator):
        """测试验证有效会话"""
        session = Session(
            id=1,
            original_question="测试问题",
            refined_question="优化后的问题",
            timestamp=datetime.now(),
            completed=False,
        )

        data_validator.validate_session(session)

    def test_validate_session_empty_question(self, data_validator):
        """测试验证空问题"""
        session = Session(
            id=1,
            original_question="",
            refined_question="优化后的问题",
            timestamp=datetime.now(),
            completed=False,
        )

        with pytest.raises(ValueError, match="原始问题不能为空"):
            data_validator.validate_session(session)

    def test_validate_session_whitespace_question(self, data_validator):
        """测试验证空白问题"""
        session = Session(
            id=1,
            original_question="   ",
            refined_question="优化后的问题",
            timestamp=datetime.now(),
            completed=False,
        )

        with pytest.raises(ValueError, match="原始问题不能为空"):
            data_validator.validate_session(session)

    def test_validate_session_too_long_question(self, data_validator):
        """测试验证过长问题"""
        session = Session(
            id=1,
            original_question="x" * 1001,
            refined_question="优化后的问题",
            timestamp=datetime.now(),
            completed=False,
        )

        with pytest.raises(ValueError, match="问题的长度不能超过1000个字符"):
            data_validator.validate_session(session)

    def test_validate_tool_result_valid(self, data_validator):
        """测试验证有效工具结果"""
        result = ToolResult(
            id=1,
            session_id=1,
            tool_name="test_tool",
            success=True,
            answer="测试答案",
            error_message=None,
            execution_time=1.5,
            timestamp=datetime.now(),
        )

        data_validator.validate_tool_result(result)

    def test_validate_tool_result_empty_tool_name(self, data_validator):
        """测试验证空工具名称"""
        result = ToolResult(
            id=1,
            session_id=1,
            tool_name="",
            success=True,
            answer="测试答案",
            error_message=None,
            execution_time=1.5,
            timestamp=datetime.now(),
        )

        with pytest.raises(ValueError, match="工具名称不能为空"):
            data_validator.validate_tool_result(result)

    def test_validate_tool_result_invalid_session_id(self, data_validator):
        """测试验证无效会话ID"""
        result = ToolResult(
            id=1,
            session_id=0,
            tool_name="test_tool",
            success=True,
            answer="测试答案",
            error_message=None,
            execution_time=1.5,
            timestamp=datetime.now(),
        )

        with pytest.raises(ValueError, match="会话ID必须大于0"):
            data_validator.validate_tool_result(result)

    def test_validate_tool_result_negative_execution_time(self, data_validator):
        """测试验证负执行时间"""
        result = ToolResult(
            id=1,
            session_id=1,
            tool_name="test_tool",
            success=True,
            answer="测试答案",
            error_message=None,
            execution_time=-1.0,
            timestamp=datetime.now(),
        )

        with pytest.raises(ValueError, match="执行时间不能为负数"):
            data_validator.validate_tool_result(result)

    def test_validate_tool_result_success_without_answer(self, data_validator):
        """测试验证成功结果无答案"""
        result = ToolResult(
            id=1,
            session_id=1,
            tool_name="test_tool",
            success=True,
            answer=None,
            error_message=None,
            execution_time=1.5,
            timestamp=datetime.now(),
        )

        with pytest.raises(ValueError, match="成功的工具结果必须包含答案"):
            data_validator.validate_tool_result(result)

    def test_validate_tool_result_failure_without_error(self, data_validator):
        """测试验证失败结果无错误信息"""
        result = ToolResult(
            id=1,
            session_id=1,
            tool_name="test_tool",
            success=False,
            answer=None,
            error_message=None,
            execution_time=1.5,
            timestamp=datetime.now(),
        )

        with pytest.raises(ValueError, match="失败的工具结果必须包含错误信息"):
            data_validator.validate_tool_result(result)

    def test_validate_analysis_result_valid(self, data_validator):
        """测试验证有效分析结果"""
        result = AnalysisResult(
            id=1,
            session_id=1,
            similarity_matrix=[[1.0, 0.8], [0.8, 1.0]],
            consensus_scores={"tool1": 0.9},
            key_points=["关键点1"],
            differences=["差异1"],
            comprehensive_summary="综合总结",
            final_conclusion="最终结论",
            timestamp=datetime.now(),
        )

        data_validator.validate_analysis_result(result)

    def test_validate_analysis_result_invalid_session_id(self, data_validator):
        """测试验证无效会话ID"""
        result = AnalysisResult(
            id=1,
            session_id=0,
            similarity_matrix=[[1.0, 0.8], [0.8, 1.0]],
            consensus_scores={"tool1": 0.9},
            key_points=["关键点1"],
            differences=["差异1"],
            comprehensive_summary="综合总结",
            final_conclusion="最终结论",
            timestamp=datetime.now(),
        )

        with pytest.raises(ValueError, match="会话ID必须大于0"):
            data_validator.validate_analysis_result(result)

    def test_validate_analysis_result_empty_similarity_matrix(self, data_validator):
        """测试验证空相似度矩阵"""
        result = AnalysisResult(
            id=1,
            session_id=1,
            similarity_matrix=[],
            consensus_scores={"tool1": 0.9},
            key_points=["关键点1"],
            differences=["差异1"],
            comprehensive_summary="综合总结",
            final_conclusion="最终结论",
            timestamp=datetime.now(),
        )

        with pytest.raises(ValueError, match="相似度矩阵不能为空"):
            data_validator.validate_analysis_result(result)

    def test_validate_analysis_result_empty_summary(self, data_validator):
        """测试验证空总结"""
        result = AnalysisResult(
            id=1,
            session_id=1,
            similarity_matrix=[[1.0, 0.8], [0.8, 1.0]],
            consensus_scores={"tool1": 0.9},
            key_points=["关键点1"],
            differences=["差异1"],
            comprehensive_summary="",
            final_conclusion="最终结论",
            timestamp=datetime.now(),
        )

        with pytest.raises(ValueError, match="综合总结不能为空"):
            data_validator.validate_analysis_result(result)

    def test_validate_analysis_result_empty_conclusion(self, data_validator):
        """测试验证空结论"""
        result = AnalysisResult(
            id=1,
            session_id=1,
            similarity_matrix=[[1.0, 0.8], [0.8, 1.0]],
            consensus_scores={"tool1": 0.9},
            key_points=["关键点1"],
            differences=["差异1"],
            comprehensive_summary="综合总结",
            final_conclusion="",
            timestamp=datetime.now(),
        )

        with pytest.raises(ValueError, match="最终结论不能为空"):
            data_validator.validate_analysis_result(result)

    def test_validate_batch_sessions_valid(self, data_validator):
        """测试验证批量有效会话"""
        sessions = [
            Session(
                id=i,
                original_question=f"问题{i}",
                refined_question=f"优化问题{i}",
                timestamp=datetime.now(),
                completed=False,
            )
            for i in range(1, 4)
        ]

        data_validator.validate_batch_sessions(sessions)

    def test_validate_batch_sessions_empty(self, data_validator):
        """测试验证空会话列表"""
        with pytest.raises(ValueError, match="会话列表不能为空"):
            data_validator.validate_batch_sessions([])

    def test_validate_batch_sessions_invalid(self, data_validator):
        """测试验证批量无效会话"""
        sessions = [
            Session(
                id=1,
                original_question="",
                refined_question="优化问题",
                timestamp=datetime.now(),
                completed=False,
            )
        ]

        with pytest.raises(ValueError, match="原始问题不能为空"):
            data_validator.validate_batch_sessions(sessions)

    def test_validate_batch_tool_results_valid(self, data_validator):
        """测试验证批量有效工具结果"""
        results = [
            ToolResult(
                id=i,
                session_id=1,
                tool_name=f"tool{i}",
                success=True,
                answer=f"答案{i}",
                error_message=None,
                execution_time=1.0,
                timestamp=datetime.now(),
            )
            for i in range(1, 4)
        ]

        data_validator.validate_batch_tool_results(results)

    def test_validate_batch_tool_results_empty(self, data_validator):
        """测试验证空工具结果列表"""
        with pytest.raises(ValueError, match="工具结果列表不能为空"):
            data_validator.validate_batch_tool_results([])

    def test_validate_batch_tool_results_invalid(self, data_validator):
        """测试验证批量无效工具结果"""
        results = [
            ToolResult(
                id=1,
                session_id=1,
                tool_name="",
                success=True,
                answer="答案",
                error_message=None,
                execution_time=1.0,
                timestamp=datetime.now(),
            )
        ]

        with pytest.raises(ValueError, match="工具名称不能为空"):
            data_validator.validate_batch_tool_results(results)

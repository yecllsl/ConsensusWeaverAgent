"""测试领域模型"""

from datetime import datetime

from src.models.entities import AnalysisResult, Session, ToolResult


class TestSession:
    """测试Session实体"""

    def test_session_creation(self):
        """测试创建会话"""
        session = Session(
            id=1,
            original_question="测试问题",
            refined_question="优化后的问题",
            timestamp=datetime.now(),
            completed=False,
        )
        assert session.id == 1
        assert session.original_question == "测试问题"
        assert session.refined_question == "优化后的问题"
        assert session.completed is False

    def test_session_with_defaults(self):
        """测试使用默认值创建会话"""
        session = Session(
            id=1,
            original_question="测试问题",
            refined_question="优化后的问题",
            timestamp=datetime.now(),
        )
        assert session.completed is False


class TestToolResult:
    """测试ToolResult实体"""

    def test_tool_result_creation(self):
        """测试创建工具结果"""
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
        assert result.id == 1
        assert result.session_id == 1
        assert result.tool_name == "test_tool"
        assert result.success is True
        assert result.answer == "测试答案"
        assert result.error_message is None
        assert result.execution_time == 1.5

    def test_tool_result_failure(self):
        """测试创建失败的工具结果"""
        result = ToolResult(
            id=1,
            session_id=1,
            tool_name="test_tool",
            success=False,
            answer=None,
            error_message="执行失败",
            execution_time=0.5,
            timestamp=datetime.now(),
        )
        assert result.success is False
        assert result.answer is None
        assert result.error_message == "执行失败"


class TestAnalysisResult:
    """测试AnalysisResult实体"""

    def test_analysis_result_creation(self):
        """测试创建分析结果"""
        result = AnalysisResult(
            id=1,
            session_id=1,
            similarity_matrix=[[1.0, 0.8], [0.8, 1.0]],
            consensus_scores={"tool1": 0.9, "tool2": 0.85},
            key_points=[{"source": "tool1", "point": "观点1"}],
            differences=[],
            comprehensive_summary="综合总结",
            final_conclusion="最终结论",
            timestamp=datetime.now(),
        )
        assert result.id == 1
        assert result.session_id == 1
        assert len(result.similarity_matrix) == 2
        assert result.consensus_scores["tool1"] == 0.9
        assert len(result.key_points) == 1
        assert result.comprehensive_summary == "综合总结"
        assert result.final_conclusion == "最终结论"

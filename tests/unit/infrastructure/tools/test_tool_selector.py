import json
import os
import tempfile
from unittest.mock import MagicMock

import pytest

from src.infrastructure.config.config_manager import ConfigManager, ExternalToolConfig
from src.infrastructure.tools.tool_selector import (
    ToolPerformanceMetrics,
    ToolRecommendation,
    ToolSelector,
    ToolUsageStats,
)


@pytest.fixture
def mock_config_manager():
    """创建模拟的配置管理器"""
    config_manager = MagicMock(spec=ConfigManager)
    config = MagicMock()
    config.external_tools = [
        ExternalToolConfig(
            name="iflow",
            command="iflow",
            args="ask",
            needs_internet=True,
            priority=1,
            enabled=True,
        ),
        ExternalToolConfig(
            name="codebuddy",
            command="codebuddy",
            args="ask",
            needs_internet=True,
            priority=2,
            enabled=True,
        ),
    ]
    config_manager.get_config.return_value = config
    return config_manager


@pytest.fixture
def tool_selector(mock_config_manager):
    """创建工具选择器实例"""
    selector = ToolSelector(mock_config_manager)
    selector.metrics = {}
    return selector


class TestToolSelector:
    """测试智能工具选择器"""

    def test_init(self, tool_selector):
        """测试初始化"""
        assert tool_selector.config is not None
        assert isinstance(tool_selector.metrics, dict)
        assert "iflow" in tool_selector.tool_type_mapping
        assert "codebuddy" in tool_selector.tool_type_mapping

    def test_detect_question_type_code(self, tool_selector):
        """测试检测问题类型（代码）"""
        question = "如何编写一个Python函数来计算斐波那契数列？"
        question_type = tool_selector._detect_question_type(question)

        assert question_type == "code"

    def test_detect_question_type_general(self, tool_selector):
        """测试检测问题类型（通用）"""
        question = "什么是人工智能？"
        question_type = tool_selector._detect_question_type(question)

        assert question_type == "general"

    def test_detect_question_type_analysis(self, tool_selector):
        """测试检测问题类型（分析）"""
        question = "请分析一下Python和Java的优缺点"
        question_type = tool_selector._detect_question_type(question)

        assert question_type == "analysis"

    def test_detect_question_type_default(self, tool_selector):
        """测试检测问题类型（默认）"""
        question = "这是一个普通的问题"
        question_type = tool_selector._detect_question_type(question)

        assert question_type == "general"

    def test_calculate_tool_score(self, tool_selector):
        """测试计算工具分数"""
        score = tool_selector._calculate_tool_score("iflow", "general")

        assert 0 <= score <= 1

    def test_select_tools(self, tool_selector):
        """测试选择工具"""
        question = "如何编写一个Python函数？"
        recommendations = tool_selector.select_tools(question, max_tools=2)

        assert len(recommendations) <= 2
        assert all(isinstance(r, ToolRecommendation) for r in recommendations)
        assert all(0 <= r.score <= 1 for r in recommendations)

    def test_select_tools_sorted_by_score(self, tool_selector):
        """测试选择工具（按分数排序）"""
        question = "什么是机器学习？"
        recommendations = tool_selector.select_tools(question, max_tools=2)

        if len(recommendations) > 1:
            assert recommendations[0].score >= recommendations[1].score

    def test_record_tool_execution(self, tool_selector):
        """测试记录工具执行"""
        tool_selector.record_tool_execution("iflow", success=True, execution_time=1.5)

        assert "iflow" in tool_selector.metrics
        assert tool_selector.metrics["iflow"].total_calls == 1
        assert tool_selector.metrics["iflow"].successful_calls == 1
        assert tool_selector.metrics["iflow"].failed_calls == 0
        assert tool_selector.metrics["iflow"].average_execution_time == 1.5
        assert tool_selector.metrics["iflow"].success_rate == 1.0

    def test_record_tool_execution_failure(self, tool_selector):
        """测试记录工具执行（失败）"""
        tool_selector.record_tool_execution("iflow", success=False, execution_time=2.0)

        assert tool_selector.metrics["iflow"].total_calls == 1
        assert tool_selector.metrics["iflow"].successful_calls == 0
        assert tool_selector.metrics["iflow"].failed_calls == 1
        assert tool_selector.metrics["iflow"].average_execution_time == 2.0
        assert tool_selector.metrics["iflow"].success_rate == 0.0

    def test_record_tool_execution_multiple(self, tool_selector):
        """测试记录工具执行（多次）"""
        tool_selector.record_tool_execution("iflow", success=True, execution_time=1.0)
        tool_selector.record_tool_execution("iflow", success=True, execution_time=2.0)
        tool_selector.record_tool_execution("iflow", success=False, execution_time=3.0)

        assert tool_selector.metrics["iflow"].total_calls == 3
        assert tool_selector.metrics["iflow"].successful_calls == 2
        assert tool_selector.metrics["iflow"].failed_calls == 1
        assert tool_selector.metrics["iflow"].average_execution_time == 2.0
        assert tool_selector.metrics["iflow"].success_rate == 2 / 3

    def test_get_usage_stats(self, tool_selector):
        """测试获取使用统计"""
        tool_selector.record_tool_execution("iflow", success=True, execution_time=1.5)
        tool_selector.record_tool_execution(
            "codebuddy", success=False, execution_time=2.0
        )

        stats = tool_selector.get_usage_stats()

        assert len(stats) == 2
        assert all(isinstance(s, ToolUsageStats) for s in stats)

        iflow_stats = next((s for s in stats if s.tool_name == "iflow"), None)
        assert iflow_stats is not None
        assert iflow_stats.usage_count == 1
        assert iflow_stats.success_rate == 1.0
        assert iflow_stats.avg_execution_time == 1.5

    def test_get_optimization_suggestions(self, tool_selector):
        """测试获取优化建议"""
        tool_selector.record_tool_execution("iflow", success=False, execution_time=15.0)
        tool_selector.record_tool_execution("iflow", success=False, execution_time=15.0)
        tool_selector.record_tool_execution("iflow", success=False, execution_time=15.0)
        tool_selector.record_tool_execution("iflow", success=False, execution_time=15.0)
        tool_selector.record_tool_execution("iflow", success=True, execution_time=15.0)

        suggestions = tool_selector.get_optimization_suggestions()

        assert len(suggestions) > 0
        assert any("iflow" in s for s in suggestions)

    def test_get_optimization_suggestions_no_issues(self, tool_selector):
        """测试获取优化建议（无问题）"""
        tool_selector.record_tool_execution("iflow", success=True, execution_time=1.0)

        suggestions = tool_selector.get_optimization_suggestions()

        assert len(suggestions) == 1
        assert "运行良好" in suggestions[0]

    def test_reset_metrics_single_tool(self, tool_selector):
        """测试重置工具性能指标（单个工具）"""
        tool_selector.record_tool_execution("iflow", success=True, execution_time=1.5)
        tool_selector.record_tool_execution(
            "codebuddy", success=True, execution_time=2.0
        )

        tool_selector.reset_metrics("iflow")

        assert "iflow" not in tool_selector.metrics
        assert "codebuddy" in tool_selector.metrics

    def test_reset_metrics_all(self, tool_selector):
        """测试重置所有工具性能指标"""
        tool_selector.record_tool_execution("iflow", success=True, execution_time=1.5)
        tool_selector.record_tool_execution(
            "codebuddy", success=True, execution_time=2.0
        )

        tool_selector.reset_metrics()

        assert len(tool_selector.metrics) == 0

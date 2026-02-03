#!/usr/bin/env python3
"""
测试共识分析器模块
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 将项目根目录添加到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from src.core.analyzer.consensus_analyzer import ConsensusAnalyzer


def test_difference_identification():
    """测试分歧点识别功能"""
    # 创建模拟配置管理器
    mock_config_manager = MagicMock()
    mock_config = MagicMock()
    mock_config_manager.get_config.return_value = mock_config

    # 创建模拟LLM服务
    mock_llm_service = MagicMock()

    # 模拟LLM返回带有代码块标记的响应
    mock_response = """```json
[
  {
    "content": "The first answer lists six collaboration modes, including centralized, "
                "distributed, hierarchical, alliance, competitive and mixed.",
    "sources": ["iflow", "codebuddy", "qwen"]
  },
  {
    "content": "The second answer also mentions six collaboration modes: hierarchical, "
                "equal, pipeline, competition, consensus and mixed.",
    "sources": ["iflow", "codebuddy"]
  }
]
```"""

    mock_llm_service.generate_response.return_value = mock_response

    # 创建模拟数据管理器
    mock_data_manager = MagicMock()

    # 创建ConsensusAnalyzer实例
    analyzer = ConsensusAnalyzer(mock_llm_service, mock_data_manager)

    # 模拟工具结果
    tool_results = [
        {
            "tool_name": "iflow",
            "answer": "This is a test answer from iflow.",
            "success": True,
        },
        {
            "tool_name": "codebuddy",
            "answer": "This is a test answer from codebuddy.",
            "success": True,
        },
        {
            "tool_name": "qwen",
            "answer": "This is a test answer from qwen.",
            "success": True,
        },
    ]

    try:
        # 调用分歧点识别方法
        differences = analyzer._identify_differences(tool_results)
        print("测试成功！")
        print(f"解析后的分歧点: {json.dumps(differences, indent=2)}")
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


class TestConsensusAnalyzer:
    """测试ConsensusAnalyzer类"""

    def setup_method(self):
        """设置测试方法"""
        self.mock_llm_service = MagicMock()
        self.mock_data_manager = MagicMock()
        self.analyzer = ConsensusAnalyzer(self.mock_llm_service, self.mock_data_manager)

    def test_initialization(self):
        """测试初始化"""
        assert self.analyzer.llm_service == self.mock_llm_service
        assert self.analyzer.data_manager == self.mock_data_manager

    def test_analyze_consensus_success(self):
        """测试成功分析共识"""
        tool_results = [
            {
                "tool_name": "iflow",
                "answer": "Python is a programming language",
                "success": True,
            },
            {
                "tool_name": "qwen",
                "answer": "Python is a high-level programming language",
                "success": True,
            },
        ]

        self.mock_data_manager.save_analysis_result.return_value = None

        with (
            patch.object(
                self.analyzer,
                "_calculate_similarity_matrix",
                return_value=[[1.0, 0.8], [0.8, 1.0]],
            ),
            patch.object(
                self.analyzer,
                "_calculate_consensus_scores",
                return_value={"iflow": 90.0, "qwen": 90.0},
            ),
            patch.object(self.analyzer, "_extract_key_points", return_value=[]),
            patch.object(self.analyzer, "_identify_differences", return_value=[]),
            patch.object(
                self.analyzer, "_generate_comprehensive_summary", return_value="总结"
            ),
            patch.object(
                self.analyzer, "_generate_final_conclusion", return_value="结论"
            ),
        ):
            result = self.analyzer.analyze_consensus(1, "测试问题", tool_results)

            assert result.session_id == 1
            assert result.comprehensive_summary == "总结"
            assert result.final_conclusion == "结论"

    def test_analyze_consensus_no_successful_results(self):
        """测试没有成功结果的情况"""
        tool_results = [
            {
                "tool_name": "iflow",
                "answer": "错误",
                "success": False,
            },
        ]

        with pytest.raises(ValueError):
            self.analyzer.analyze_consensus(1, "测试问题", tool_results)

    def test_calculate_similarity_matrix(self):
        """测试计算相似度矩阵"""
        tool_results = [
            {
                "tool_name": "iflow",
                "answer": "Python is a programming language",
                "success": True,
            },
            {
                "tool_name": "qwen",
                "answer": "Python is a programming language",
                "success": True,
            },
        ]

        similarity_matrix = self.analyzer._calculate_similarity_matrix(tool_results)

        assert similarity_matrix.shape == (2, 2)
        assert similarity_matrix[0, 0] == 1.0
        assert similarity_matrix[1, 1] == 1.0

    def test_calculate_consensus_scores(self):
        """测试计算共识度评分"""
        tool_results = [
            {
                "tool_name": "iflow",
                "answer": "Python is a programming language",
                "success": True,
            },
            {
                "tool_name": "qwen",
                "answer": "Python is a programming language",
                "success": True,
            },
        ]

        similarity_matrix = [[1.0, 0.9], [0.9, 1.0]]

        scores = self.analyzer._calculate_consensus_scores(
            tool_results, similarity_matrix
        )

        assert "iflow" in scores
        assert "qwen" in scores
        assert scores["iflow"] > 0
        assert scores["qwen"] > 0

    def test_extract_key_points_success(self):
        """测试成功提取核心观点"""
        tool_results = [
            {
                "tool_name": "iflow",
                "answer": "Python is a programming language",
                "success": True,
            },
        ]

        mock_response = json.dumps(
            [{"content": "Python is a programming language", "sources": ["iflow"]}]
        )

        self.mock_llm_service.generate_response.return_value = mock_response

        key_points = self.analyzer._extract_key_points(tool_results)

        assert isinstance(key_points, list)

    def test_extract_key_points_empty_response(self):
        """测试空响应时的核心观点提取"""
        tool_results = [
            {
                "tool_name": "iflow",
                "answer": "Python is a programming language",
                "success": True,
            },
        ]

        self.mock_llm_service.generate_response.return_value = ""

        key_points = self.analyzer._extract_key_points(tool_results)

        assert isinstance(key_points, list)

    def test_extract_key_points_invalid_json(self):
        """测试无效JSON时的核心观点提取"""
        tool_results = [
            {
                "tool_name": "iflow",
                "answer": "Python is a programming language",
                "success": True,
            },
        ]

        self.mock_llm_service.generate_response.return_value = "不是有效的JSON"

        key_points = self.analyzer._extract_key_points(tool_results)

        assert isinstance(key_points, list)

    def test_simple_key_point_extraction(self):
        """测试简单的核心观点提取"""
        tool_results = [
            {
                "tool_name": "iflow",
                "answer": "Python is a programming language",
                "success": True,
            },
            {
                "tool_name": "qwen",
                "answer": "Python is a high-level programming language",
                "success": True,
            },
        ]

        key_points = self.analyzer._simple_key_point_extraction(tool_results)

        assert isinstance(key_points, list)
        assert len(key_points) > 0

    def test_identify_differences_success(self):
        """测试成功识别分歧点"""
        tool_results = [
            {
                "tool_name": "iflow",
                "answer": "Python is a programming language",
                "success": True,
            },
        ]

        mock_response = json.dumps(
            [{"content": "Different opinions on Python", "sources": ["iflow", "qwen"]}]
        )

        self.mock_llm_service.generate_response.return_value = mock_response

        differences = self.analyzer._identify_differences(tool_results)

        assert isinstance(differences, list)

    def test_identify_differences_empty_response(self):
        """测试空响应时的分歧点识别"""
        tool_results = [
            {
                "tool_name": "iflow",
                "answer": "Python is a programming language",
                "success": True,
            },
        ]

        self.mock_llm_service.generate_response.return_value = ""

        differences = self.analyzer._identify_differences(tool_results)

        assert differences == []

    def test_identify_differences_invalid_json(self):
        """测试无效JSON时的分歧点识别"""
        tool_results = [
            {
                "tool_name": "iflow",
                "answer": "Python is a programming language",
                "success": True,
            },
        ]

        self.mock_llm_service.generate_response.return_value = "不是有效的JSON"

        differences = self.analyzer._identify_differences(tool_results)

        assert differences == []

    def test_generate_comprehensive_summary(self):
        """测试生成综合总结"""
        question = "什么是Python？"
        tool_results = [
            {
                "tool_name": "iflow",
                "answer": "Python is a programming language",
                "success": True,
            },
        ]
        key_points = [
            {"content": "Python is a programming language", "sources": ["iflow"]}
        ]
        differences = []

        self.mock_llm_service.generate_response.return_value = "Python是一种编程语言"

        summary = self.analyzer._generate_comprehensive_summary(
            question, tool_results, key_points, differences
        )

        assert isinstance(summary, str)

    def test_generate_final_conclusion(self):
        """测试生成最终结论"""
        comprehensive_summary = "Python是一种编程语言"
        consensus_scores = {"iflow": 90.0, "qwen": 85.0}

        self.mock_llm_service.generate_response.return_value = (
            "结论：Python是一种编程语言"
        )

        conclusion = self.analyzer._generate_final_conclusion(
            comprehensive_summary, consensus_scores
        )

        assert isinstance(conclusion, str)

    def test_preprocess_text(self):
        """测试文本预处理"""
        text = "Python is a programming language"

        processed = self.analyzer._preprocess_text(text)

        assert isinstance(processed, list)
        assert len(processed) > 0

    def test_get_analysis_result_success(self):
        """测试成功获取分析结果"""
        mock_result = MagicMock()
        mock_result.session_id = 1
        mock_result.similarity_matrix = [[1.0]]
        mock_result.consensus_scores = {"iflow": 90.0}
        mock_result.key_points = []
        mock_result.differences = []
        mock_result.comprehensive_summary = "总结"
        mock_result.final_conclusion = "结论"

        self.mock_data_manager.get_analysis_result.return_value = mock_result

        result = self.analyzer.get_analysis_result(1)

        assert result is not None
        assert result.session_id == 1

    def test_get_analysis_result_not_found(self):
        """测试获取不存在的分析结果"""
        self.mock_data_manager.get_analysis_result.return_value = None

        result = self.analyzer.get_analysis_result(1)

        assert result is None


if __name__ == "__main__":
    test_difference_identification()

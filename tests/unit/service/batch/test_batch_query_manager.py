import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.service.batch.batch_query_manager import (
    BatchQueryManager,
    BatchQueryResult,
    BatchQuestion,
)


@pytest.fixture
def mock_query_executor():
    """创建模拟的查询执行器"""
    executor = MagicMock()
    executor.tool_manager = MagicMock()
    executor.tool_manager.get_enabled_tools.return_value = [
        {"name": "iflow"},
        {"name": "codebuddy"},
    ]
    return executor


@pytest.fixture
def mock_data_manager():
    """创建模拟的数据管理器"""
    data_manager = MagicMock()
    data_manager.create_session.return_value = 1
    return data_manager


@pytest.fixture
def mock_multi_format_reporter():
    """创建模拟的多格式报告器"""
    return MagicMock()


@pytest.fixture
def batch_query_manager(
    mock_query_executor, mock_data_manager, mock_multi_format_reporter
):
    """创建批量查询管理器实例"""
    return BatchQueryManager(
        mock_query_executor, mock_data_manager, mock_multi_format_reporter
    )


class TestBatchQueryManager:
    """测试批量查询管理器"""

    def test_load_questions_from_file_string_list(self, batch_query_manager):
        """测试从文件加载问题（字符串列表）"""
        questions_data = ["问题1", "问题2", "问题3"]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(questions_data, f, ensure_ascii=False)
            temp_file = f.name

        try:
            questions = batch_query_manager.load_questions_from_file(temp_file)

            assert len(questions) == 3
            assert questions[0].question == "问题1"
            assert questions[1].question == "问题2"
            assert questions[2].question == "问题3"
            assert questions[0].priority == "medium"
        finally:
            os.unlink(temp_file)

    def test_load_questions_from_file_dict_list(self, batch_query_manager):
        """测试从文件加载问题（字典列表）"""
        questions_data = [
            {"question": "问题1", "priority": "high"},
            {"question": "问题2", "priority": "low"},
            {"question": "问题3"},
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(questions_data, f, ensure_ascii=False)
            temp_file = f.name

        try:
            questions = batch_query_manager.load_questions_from_file(temp_file)

            assert len(questions) == 3
            assert questions[0].question == "问题1"
            assert questions[0].priority == "high"
            assert questions[1].question == "问题2"
            assert questions[1].priority == "low"
            assert questions[2].question == "问题3"
            assert questions[2].priority == "medium"
        finally:
            os.unlink(temp_file)

    def test_load_questions_from_file_not_found(self, batch_query_manager):
        """测试从不存在的文件加载问题"""
        with pytest.raises(FileNotFoundError):
            batch_query_manager.load_questions_from_file("nonexistent.json")

    def test_load_questions_from_file_invalid_json(self, batch_query_manager):
        """测试从无效的JSON文件加载问题"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("invalid json")
            temp_file = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                batch_query_manager.load_questions_from_file(temp_file)
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_execute_batch_queries(self, batch_query_manager, mock_data_manager):
        """测试执行批量查询"""
        questions = [
            BatchQuestion(question="问题1"),
            BatchQuestion(question="问题2"),
        ]

        mock_result = MagicMock()
        mock_result.completed = True
        mock_result.tool_results = []

        batch_query_manager.query_executor.execute_queries = AsyncMock(
            return_value=mock_result
        )

        results = await batch_query_manager.execute_batch_queries(
            questions, max_concurrent=2
        )

        assert len(results) == 2
        assert results[0].question == "问题1"
        assert results[1].question == "问题2"
        assert results[0].success
        assert results[1].success

    @pytest.mark.asyncio
    async def test_execute_batch_queries_with_error(
        self, batch_query_manager, mock_data_manager
    ):
        """测试执行批量查询（带错误）"""
        questions = [
            BatchQuestion(question="问题1"),
            BatchQuestion(question="问题2"),
        ]

        batch_query_manager.query_executor.execute_queries = AsyncMock(
            side_effect=[MagicMock(completed=True, tool_results=[]), Exception("错误")]
        )

        results = await batch_query_manager.execute_batch_queries(
            questions, max_concurrent=2
        )

        assert len(results) == 2
        assert results[0].success
        assert not results[1].success
        assert results[1].error_message == "错误"

    def test_generate_batch_report_markdown(self, batch_query_manager):
        """测试生成批量查询报告（Markdown格式）"""
        results = [
            BatchQueryResult(
                question="问题1",
                priority="high",
                session_id=1,
                success=True,
                execution_time=1.5,
            ),
            BatchQueryResult(
                question="问题2",
                priority="low",
                session_id=2,
                success=False,
                execution_time=2.0,
                error_message="错误",
            ),
        ]

        report = batch_query_manager.generate_batch_report(results, "markdown")

        assert report.total_questions == 2
        assert report.success_count == 1
        assert report.failure_count == 1
        assert report.total_execution_time == 3.5
        assert "# 批量查询报告" in report.content
        assert "问题1" in report.content
        assert "问题2" in report.content

    def test_generate_batch_report_json(self, batch_query_manager):
        """测试生成批量查询报告（JSON格式）"""
        results = [
            BatchQueryResult(
                question="问题1",
                priority="high",
                session_id=1,
                success=True,
                execution_time=1.5,
            ),
        ]

        report = batch_query_manager.generate_batch_report(results, "json")

        assert report.total_questions == 1
        assert report.success_count == 1

        report_data = json.loads(report.content)
        assert report_data["summary"]["total_questions"] == 1
        assert report_data["summary"]["success_count"] == 1
        assert len(report_data["results"]) == 1

    def test_generate_batch_report_text(self, batch_query_manager):
        """测试生成批量查询报告（文本格式）"""
        results = [
            BatchQueryResult(
                question="问题1",
                priority="high",
                session_id=1,
                success=True,
                execution_time=1.5,
            ),
        ]

        report = batch_query_manager.generate_batch_report(results, "text")

        assert report.total_questions == 1
        assert "批量查询报告" in report.content
        assert "问题1" in report.content

    def test_generate_batch_report_invalid_format(self, batch_query_manager):
        """测试生成批量查询报告（无效格式）"""
        results = [
            BatchQueryResult(
                question="问题1",
                priority="high",
                session_id=1,
                success=True,
                execution_time=1.5,
            ),
        ]

        with pytest.raises(ValueError, match="不支持的报告格式"):
            batch_query_manager.generate_batch_report(results, "invalid_format")

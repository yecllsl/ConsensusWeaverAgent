"""测试数据仓库"""

import sqlite3
from datetime import datetime
from unittest.mock import Mock

import pytest

from src.infrastructure.data.data_validator import DataValidator
from src.infrastructure.data.repositories.sqlite_repository import (
    SqliteAnalysisResultRepository,
    SqliteSessionRepository,
    SqliteToolResultRepository,
)
from src.models.entities import AnalysisResult, Session, ToolResult


@pytest.fixture
def mock_connection():
    """模拟数据库连接"""
    conn = Mock(spec=sqlite3.Connection)
    cursor = Mock(spec=sqlite3.Cursor)
    conn.cursor.return_value = cursor
    return conn, cursor


@pytest.fixture
def data_validator():
    """数据验证器"""
    return DataValidator()


class TestSqliteSessionRepository:
    """测试会话仓库"""

    @pytest.mark.asyncio
    async def test_add_session(self, mock_connection, data_validator):
        """测试添加会话"""
        conn, cursor = mock_connection
        cursor.lastrowid = 1

        repo = SqliteSessionRepository(conn, data_validator)
        session = Session(
            id=0,
            original_question="测试问题",
            refined_question="优化后的问题",
            timestamp=datetime.now(),
            completed=False,
        )

        result = await repo.add(session)

        assert result == 1
        cursor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_session(self, mock_connection, data_validator):
        """测试更新会话"""
        conn, cursor = mock_connection
        repo = SqliteSessionRepository(conn, data_validator)
        session = Session(
            id=1,
            original_question="测试问题",
            refined_question="更新后的问题",
            timestamp=datetime.now(),
            completed=True,
        )

        await repo.update(session)

        cursor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session(self, mock_connection, data_validator):
        """测试删除会话"""
        conn, cursor = mock_connection
        repo = SqliteSessionRepository(conn, data_validator)

        await repo.delete(1)

        cursor.execute.assert_called_once_with(
            "DELETE FROM sessions WHERE id = ?", (1,)
        )

    @pytest.mark.asyncio
    async def test_get_by_id(self, mock_connection, data_validator):
        """测试根据ID获取会话"""
        conn, cursor = mock_connection
        cursor.fetchone.return_value = (
            1,
            "测试问题",
            "优化后的问题",
            datetime.now().isoformat(),
            1,
        )

        repo = SqliteSessionRepository(conn, data_validator)
        session = await repo.get_by_id(1)

        assert session is not None
        assert session.id == 1
        assert session.original_question == "测试问题"


class TestSqliteToolResultRepository:
    """测试工具结果仓库"""

    @pytest.mark.asyncio
    async def test_add_tool_result(self, mock_connection, data_validator):
        """测试添加工具结果"""
        conn, cursor = mock_connection
        cursor.lastrowid = 1

        repo = SqliteToolResultRepository(conn, data_validator)
        result = ToolResult(
            id=0,
            session_id=1,
            tool_name="test_tool",
            success=True,
            answer="测试答案",
            error_message=None,
            execution_time=1.5,
            timestamp=datetime.now(),
        )

        result_id = await repo.add(result)

        assert result_id == 1
        cursor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_session_id(self, mock_connection, data_validator):
        """测试根据会话ID获取工具结果"""
        conn, cursor = mock_connection
        cursor.fetchall.return_value = [
            (
                1,
                1,
                "tool1",
                True,
                "答案1",
                None,
                1.0,
                datetime.now().isoformat(),
            ),
            (
                2,
                1,
                "tool2",
                True,
                "答案2",
                None,
                1.5,
                datetime.now().isoformat(),
            ),
        ]

        repo = SqliteToolResultRepository(conn, data_validator)
        results = await repo.get_by_session_id(1)

        assert len(results) == 2
        assert results[0].tool_name == "tool1"
        assert results[1].tool_name == "tool2"

    @pytest.mark.asyncio
    async def test_delete_by_session_id(self, mock_connection, data_validator):
        """测试根据会话ID删除工具结果"""
        conn, cursor = mock_connection
        repo = SqliteToolResultRepository(conn, data_validator)

        await repo.delete(1)

        cursor.execute.assert_called_once_with(
            "DELETE FROM tool_results WHERE id = ?", (1,)
        )


class TestSqliteAnalysisResultRepository:
    """测试分析结果仓库"""

    @pytest.mark.asyncio
    async def test_add_analysis_result(self, mock_connection, data_validator):
        """测试添加分析结果"""
        conn, cursor = mock_connection
        cursor.lastrowid = 1

        repo = SqliteAnalysisResultRepository(conn, data_validator)
        result = AnalysisResult(
            id=0,
            session_id=1,
            similarity_matrix=[[1.0, 0.8], [0.8, 1.0]],
            consensus_scores={"tool1": 0.9},
            key_points=[],
            differences=[],
            comprehensive_summary="总结",
            final_conclusion="结论",
            timestamp=datetime.now(),
        )

        result_id = await repo.add(result)

        assert result_id == 1
        cursor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_session_id(self, mock_connection, data_validator):
        """测试根据会话ID获取分析结果"""
        conn, cursor = mock_connection
        cursor.fetchone.return_value = (
            1,
            1,
            "[[1.0, 0.8], [0.8, 1.0]]",
            '{"tool1": 0.9}',
            "[]",
            "[]",
            "总结",
            "结论",
            datetime.now().isoformat(),
        )

        repo = SqliteAnalysisResultRepository(conn, data_validator)
        result = await repo.get_by_session_id(1)

        assert result is not None
        assert result.session_id == 1
        assert result.comprehensive_summary == "总结"

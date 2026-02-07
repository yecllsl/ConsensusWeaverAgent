"""测试工作单元模式"""
import sqlite3
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.models.entities import Session, ToolResult
from src.infrastructure.data.data_validator import DataValidator
from src.infrastructure.data.repositories.sqlite_repository import (
    SqliteSessionRepository,
    SqliteToolResultRepository,
    SqliteAnalysisResultRepository,
)
from src.infrastructure.data.unit_of_work import SqliteUnitOfWork


@pytest.fixture
def mock_connection():
    """模拟数据库连接"""
    conn = Mock(spec=sqlite3.Connection)
    cursor = Mock(spec=sqlite3.Cursor)
    conn.cursor.return_value = cursor
    conn.commit = Mock()
    conn.rollback = Mock()
    return conn, cursor


@pytest.fixture
def data_validator():
    """数据验证器"""
    return DataValidator()


class TestSqliteUnitOfWork:
    """测试工作单元"""

    def test_initialization(self, mock_connection, data_validator):
        """测试工作单元初始化"""
        conn, _ = mock_connection
        uow = SqliteUnitOfWork(conn, data_validator)

        assert uow._conn == conn
        assert uow._validator == data_validator
        assert uow._committed is False
        assert uow._rolled_back is False
        assert uow.sessions is not None
        assert uow.tool_results is not None
        assert uow.analysis_results is not None

    @pytest.mark.asyncio
    async def test_commit(self, mock_connection, data_validator):
        """测试提交事务"""
        conn, _ = mock_connection
        uow = SqliteUnitOfWork(conn, data_validator)

        await uow.commit()

        assert uow._committed is True
        conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback(self, mock_connection, data_validator):
        """测试回滚事务"""
        conn, _ = mock_connection
        uow = SqliteUnitOfWork(conn, data_validator)

        await uow.rollback()

        assert uow._rolled_back is True
        conn.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_session(self, mock_connection, data_validator):
        """测试添加会话"""
        conn, cursor = mock_connection
        cursor.lastrowid = 1
        uow = SqliteUnitOfWork(conn, data_validator)

        session = Session(
            id=0,
            original_question="测试问题",
            refined_question="优化后的问题",
            timestamp=datetime.now(),
            completed=False,
        )

        result = await uow.sessions.add(session)

        assert result == 1

    @pytest.mark.asyncio
    async def test_add_tool_result(self, mock_connection, data_validator):
        """测试添加工具结果"""
        conn, cursor = mock_connection
        cursor.lastrowid = 1
        uow = SqliteUnitOfWork(conn, data_validator)

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

        result_id = await uow.tool_results.add(result)

        assert result_id == 1

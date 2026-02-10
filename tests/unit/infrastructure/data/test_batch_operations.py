"""测试批量操作"""

import sqlite3
from datetime import datetime
from unittest.mock import Mock

import pytest

from src.infrastructure.data.batch_operations import BatchOperations


@pytest.fixture
def mock_connection():
    """模拟数据库连接"""
    conn = Mock(spec=sqlite3.Connection)
    cursor = Mock(spec=sqlite3.Cursor)
    conn.cursor.return_value = cursor
    return conn, cursor


class TestBatchOperations:
    """测试批量操作类"""

    def test_init(self, mock_connection):
        """测试初始化"""
        conn, _ = mock_connection
        batch_ops = BatchOperations(conn)

        assert batch_ops._conn is conn

    @pytest.mark.asyncio
    async def test_batch_insert_sessions(self, mock_connection):
        """测试批量插入会话"""
        conn, cursor = mock_connection
        cursor.lastrowid = 3

        batch_ops = BatchOperations(conn)

        sessions = [
            {
                "original_question": f"问题{i}",
                "refined_question": f"优化问题{i}",
                "timestamp": datetime.now().isoformat(),
                "completed": False,
            }
            for i in range(3)
        ]

        result = await batch_ops.batch_insert_sessions(sessions)

        assert len(result) == 3
        cursor.executemany.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_insert_sessions_empty(self, mock_connection):
        """测试批量插入空会话列表"""
        conn, cursor = mock_connection
        cursor.lastrowid = 0

        batch_ops = BatchOperations(conn)

        result = await batch_ops.batch_insert_sessions([])

        assert result == []

    @pytest.mark.asyncio
    async def test_batch_insert_tool_results(self, mock_connection):
        """测试批量插入工具结果"""
        conn, cursor = mock_connection
        cursor.lastrowid = 3

        batch_ops = BatchOperations(conn)

        results = [
            {
                "session_id": 1,
                "tool_name": f"tool{i}",
                "success": True,
                "answer": f"答案{i}",
                "error_message": None,
                "execution_time": 1.0,
                "timestamp": datetime.now().isoformat(),
            }
            for i in range(3)
        ]

        result = await batch_ops.batch_insert_tool_results(results)

        assert len(result) == 3
        cursor.executemany.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_insert_tool_results_empty(self, mock_connection):
        """测试批量插入空工具结果列表"""
        conn, cursor = mock_connection
        cursor.lastrowid = 0

        batch_ops = BatchOperations(conn)

        result = await batch_ops.batch_insert_tool_results([])

        assert result == []

    @pytest.mark.asyncio
    async def test_batch_delete_sessions(self, mock_connection):
        """测试批量删除会话"""
        conn, cursor = mock_connection

        batch_ops = BatchOperations(conn)

        session_ids = [1, 2, 3]
        await batch_ops.batch_delete_sessions(session_ids)

        assert cursor.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_delete_sessions_empty(self, mock_connection):
        """测试批量删除空会话ID列表"""
        conn, cursor = mock_connection

        batch_ops = BatchOperations(conn)

        await batch_ops.batch_delete_sessions([])

        assert cursor.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_update_sessions(self, mock_connection):
        """测试批量更新会话"""
        conn, cursor = mock_connection

        batch_ops = BatchOperations(conn)

        updates = [
            {
                "id": i,
                "refined_question": f"优化问题{i}",
                "completed": True,
            }
            for i in range(1, 4)
        ]

        await batch_ops.batch_update_sessions(updates)

        assert cursor.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_update_sessions_empty(self, mock_connection):
        """测试批量更新空会话列表"""
        conn, cursor = mock_connection

        batch_ops = BatchOperations(conn)

        await batch_ops.batch_update_sessions([])

        assert cursor.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_batch_insert_analysis_results(self, mock_connection):
        """测试批量插入分析结果"""
        conn, cursor = mock_connection
        cursor.lastrowid = 2

        batch_ops = BatchOperations(conn)

        results = [
            {
                "session_id": 1,
                "similarity_matrix": "[[1.0, 0.8], [0.8, 1.0]]",
                "consensus_scores": '{"tool1": 0.9}',
                "key_points": "[]",
                "differences": "[]",
                "comprehensive_summary": "总结",
                "final_conclusion": "结论",
                "timestamp": datetime.now().isoformat(),
            }
            for _ in range(2)
        ]

        result = await batch_ops.batch_insert_analysis_results(results)

        assert len(result) == 2
        cursor.executemany.assert_called_once()

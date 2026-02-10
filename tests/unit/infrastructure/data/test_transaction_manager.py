"""测试事务管理器"""

import sqlite3
from unittest.mock import Mock

import pytest

from src.infrastructure.data.transaction_manager import TransactionManager


@pytest.fixture
def mock_connection():
    """模拟数据库连接"""
    conn = Mock(spec=sqlite3.Connection)
    cursor = Mock(spec=sqlite3.Cursor)
    conn.cursor.return_value = cursor
    return conn, cursor


class TestTransactionManager:
    """测试事务管理器类"""

    def test_init(self):
        """测试初始化"""
        manager = TransactionManager(":memory:")

        assert manager.db_path == ":memory:"
        assert manager._conn is None

    def test_get_connection(self):
        """测试获取数据库连接"""
        manager = TransactionManager(":memory:")

        conn = manager._get_connection()

        assert conn is not None
        assert manager._conn is conn

    def test_close(self):
        """测试关闭数据库连接"""
        manager = TransactionManager(":memory:")

        conn = manager._get_connection()
        manager.close()

        assert manager._conn is None

    def test_context_manager(self):
        """测试上下文管理器"""
        with TransactionManager(":memory:") as manager:
            assert manager is not None
            conn = manager._get_connection()
            assert conn is not None

        assert manager._conn is None

    @pytest.mark.asyncio
    async def test_begin_transaction(self):
        """测试开始事务"""
        manager = TransactionManager(":memory:")

        async with manager.begin_transaction() as uow:
            assert uow is not None

    @pytest.mark.skip("SQLite不支持嵌套事务")
    @pytest.mark.asyncio
    async def test_begin_transaction_nested(self):
        """测试嵌套事务"""
        manager = TransactionManager(":memory:")

        async with manager.begin_transaction() as uow1:
            assert uow1 is not None

            async with manager.begin_transaction() as uow2:
                assert uow2 is not None

    @pytest.mark.asyncio
    async def test_commit_transaction(self):
        """测试提交事务"""
        manager = TransactionManager(":memory:")

        async with manager.begin_transaction() as uow:
            assert uow is not None

    @pytest.mark.asyncio
    async def test_rollback_transaction(self):
        """测试回滚事务"""
        manager = TransactionManager(":memory:")

        try:
            async with manager.begin_transaction() as uow:
                assert uow is not None
                raise ValueError("测试异常")
        except ValueError:
            pass

    @pytest.mark.asyncio
    async def test_context_manager_success(self):
        """测试上下文管理器成功执行"""
        manager = TransactionManager(":memory:")

        async with manager.begin_transaction() as uow:
            assert uow is not None

    @pytest.mark.asyncio
    async def test_context_manager_exception(self):
        """测试上下文管理器异常处理"""
        manager = TransactionManager(":memory:")

        with pytest.raises(ValueError):
            async with manager.begin_transaction() as uow:
                assert uow is not None
                raise ValueError("测试异常")

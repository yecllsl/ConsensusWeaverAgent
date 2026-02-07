"""工作单元模式实现

本模块实现了工作单元模式，用于管理事务和协调多个仓库操作。
"""

import sqlite3

from src.infrastructure.data.data_validator import DataValidator
from src.infrastructure.data.repositories.interfaces import (
    IAnalysisResultRepository,
    ISessionRepository,
    IToolResultRepository,
    IUnitOfWork,
)
from src.infrastructure.data.repositories.sqlite_repository import (
    SqliteAnalysisResultRepository,
    SqliteSessionRepository,
    SqliteToolResultRepository,
)


class SqliteUnitOfWork(IUnitOfWork):
    """SQLite工作单元实现

    管理事务和协调多个仓库操作，确保数据一致性。
    """

    def __init__(self, connection: sqlite3.Connection, validator: DataValidator):
        self._conn = connection
        self._validator = validator
        self._committed = False
        self._rolled_back = False

        self._sessions = SqliteSessionRepository(connection, validator)
        self._tool_results = SqliteToolResultRepository(connection, validator)
        self._analysis_results = SqliteAnalysisResultRepository(connection, validator)

    async def __aenter__(self) -> "IUnitOfWork":
        """进入事务上下文"""
        self._conn.execute("BEGIN TRANSACTION")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """退出事务上下文"""
        if exc_type is not None:
            await self.rollback()
        elif not self._committed and not self._rolled_back:
            await self.commit()

    async def commit(self) -> None:
        """提交事务"""
        if not self._rolled_back:
            self._conn.commit()
            self._committed = True

    async def rollback(self) -> None:
        """回滚事务"""
        if not self._committed:
            self._conn.rollback()
            self._rolled_back = True

    @property
    def sessions(self) -> ISessionRepository:
        """会话仓库"""
        return self._sessions

    @property
    def tool_results(self) -> IToolResultRepository:
        """工具结果仓库"""
        return self._tool_results

    @property
    def analysis_results(self) -> IAnalysisResultRepository:
        """分析结果仓库"""
        return self._analysis_results

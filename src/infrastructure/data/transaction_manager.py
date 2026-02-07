"""事务管理器

本模块实现了事务管理器，用于创建和管理数据库连接和工作单元。
"""

import sqlite3
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from src.infrastructure.data.data_validator import DataValidator
from src.infrastructure.data.unit_of_work import SqliteUnitOfWork


class TransactionManager:
    """事务管理器

    负责创建和管理数据库连接，提供工作单元的创建功能。
    """

    def __init__(self, db_path: str = "consensusweaver.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._validator = DataValidator()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._initialize_database()
            self._configure_database()
        return self._conn

    def _initialize_database(self) -> None:
        """初始化数据库表结构"""
        cursor = self._conn.cursor()

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_question TEXT NOT NULL,
            refined_question TEXT,
            timestamp TEXT NOT NULL,
            completed BOOLEAN DEFAULT FALSE
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS tool_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            tool_name TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            answer TEXT,
            error_message TEXT,
            execution_time REAL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            similarity_matrix TEXT NOT NULL,
            consensus_scores TEXT NOT NULL,
            key_points TEXT NOT NULL,
            differences TEXT NOT NULL,
            comprehensive_summary TEXT NOT NULL,
            final_conclusion TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
        """
        )

        self._conn.commit()

    def _configure_database(self) -> None:
        """配置数据库优化选项"""
        cursor = self._conn.cursor()

        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = -64000")
        cursor.execute("PRAGMA temp_store = MEMORY")

        self._conn.commit()

    def _create_indexes(self) -> None:
        """创建数据库索引"""
        cursor = self._conn.cursor()

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_timestamp "
            "ON sessions(timestamp DESC)"
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tool_results_session_id "
            "ON tool_results(session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tool_results_timestamp "
            "ON tool_results(timestamp DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tool_results_session_timestamp "
            "ON tool_results(session_id, timestamp DESC)"
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_results_session_id "
            "ON analysis_results(session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_results_timestamp "
            "ON analysis_results(timestamp DESC)"
        )

        self._conn.commit()

    @asynccontextmanager
    async def begin_transaction(self) -> AsyncGenerator[SqliteUnitOfWork, None]:
        """开始事务"""
        conn = self._get_connection()
        unit_of_work = SqliteUnitOfWork(conn, self._validator)
        async with unit_of_work as uow:
            yield uow

    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

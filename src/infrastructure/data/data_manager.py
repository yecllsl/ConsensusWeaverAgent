import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Any, Dict, List, Optional, cast


@dataclass
class SessionRecord:
    id: int
    original_question: str
    refined_question: str
    timestamp: datetime
    completed: bool


@dataclass
class ToolResultRecord:
    id: int
    session_id: int
    tool_name: str
    success: bool
    answer: str
    error_message: str
    execution_time: float
    timestamp: datetime


@dataclass
class AnalysisResultRecord:
    id: int
    session_id: int
    similarity_matrix: List[List[float]]
    consensus_scores: Dict[str, float]
    key_points: List[Dict[str, Any]]
    differences: List[Dict[str, Any]]
    comprehensive_summary: str
    final_conclusion: str
    timestamp: datetime


class DataManager:
    def __init__(self, db_path: str = "consensusweaver.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # 创建会话表
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_question TEXT NOT NULL,
            refined_question TEXT,
            timestamp TEXT NOT NULL,
            completed BOOLEAN DEFAULT FALSE
        )
        """)

        # 创建工具结果表
        self.cursor.execute("""
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
        """)

        # 创建分析结果表
        self.cursor.execute("""
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
        """)

        self.conn.commit()

    def close(self) -> None:
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.cursor = None
        self.conn = None

    def save_session(
        self, original_question: str, refined_question: Optional[str] = None
    ) -> int:
        """保存会话记录"""
        timestamp = datetime.now().isoformat()
        # 类型断言：cursor和conn在_init_db中已初始化，不会为None
        cursor = cast(sqlite3.Cursor, self.cursor)
        conn = cast(sqlite3.Connection, self.conn)

        cursor.execute(
            "INSERT INTO sessions "
            "(original_question, refined_question, timestamp, completed) "
            "VALUES (?, ?, ?, ?)",
            (original_question, refined_question, timestamp, False),
        )
        conn.commit()
        # 类型断言确保返回int类型
        return cast(int, cursor.lastrowid)

    def update_session(
        self,
        session_id: int,
        refined_question: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> None:
        """更新会话记录"""
        update_fields: List[str] = []
        update_values: List[Any] = []

        if refined_question is not None:
            update_fields.append("refined_question = ?")
            update_values.append(refined_question)

        if completed is not None:
            update_fields.append("completed = ?")
            update_values.append(completed)

        if update_fields:
            update_values.append(session_id)
            query = f"UPDATE sessions SET {', '.join(update_fields)} WHERE id = ?"
            # 类型断言：cursor和conn在_init_db中已初始化，不会为None
            cursor = cast(sqlite3.Cursor, self.cursor)
            conn = cast(sqlite3.Connection, self.conn)
            cursor.execute(query, update_values)
            conn.commit()

    def get_session(self, session_id: int) -> Optional[SessionRecord]:
        """获取会话记录"""
        # 类型断言：cursor在_init_db中已初始化，不会为None
        cursor = cast(sqlite3.Cursor, self.cursor)
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            return SessionRecord(
                id=row[0],
                original_question=row[1],
                refined_question=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                completed=bool(row[4]),
            )
        return None

    def get_recent_sessions(self, limit: int = 10) -> List[SessionRecord]:
        """获取最近的会话记录"""
        # 类型断言：cursor在_init_db中已初始化，不会为None
        cursor = cast(sqlite3.Cursor, self.cursor)
        cursor.execute(
            "SELECT * FROM sessions ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        return [
            SessionRecord(
                id=row[0],
                original_question=row[1],
                refined_question=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                completed=bool(row[4]),
            )
            for row in rows
        ]

    def save_tool_result(
        self,
        session_id: int,
        tool_name: str,
        success: bool,
        answer: str = "",
        error_message: str = "",
        execution_time: float = 0.0,
    ) -> int:
        """保存工具结果"""
        timestamp = datetime.now().isoformat()
        # 类型断言：cursor和conn在_init_db中已初始化，不会为None
        cursor = cast(sqlite3.Cursor, self.cursor)
        conn = cast(sqlite3.Connection, self.conn)

        cursor.execute(
            "INSERT INTO tool_results "
            "(session_id, tool_name, success, answer, "
            "error_message, execution_time, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                tool_name,
                success,
                answer,
                error_message,
                execution_time,
                timestamp,
            ),
        )
        conn.commit()
        # 类型断言确保返回int类型
        return cast(int, cursor.lastrowid)

    def get_tool_results(self, session_id: int) -> List[ToolResultRecord]:
        """获取会话的工具结果"""
        # 类型断言：cursor在_init_db中已初始化，不会为None
        cursor = cast(sqlite3.Cursor, self.cursor)
        cursor.execute("SELECT * FROM tool_results WHERE session_id = ?", (session_id,))
        rows = cursor.fetchall()
        return [
            ToolResultRecord(
                id=row[0],
                session_id=row[1],
                tool_name=row[2],
                success=bool(row[3]),
                answer=row[4],
                error_message=row[5],
                execution_time=row[6],
                timestamp=datetime.fromisoformat(row[7]),
            )
            for row in rows
        ]

    def save_analysis_result(
        self,
        session_id: int,
        similarity_matrix: List[List[float]],
        consensus_scores: Dict[str, float],
        key_points: List[Dict[str, Any]],
        differences: List[Dict[str, Any]],
        comprehensive_summary: str,
        final_conclusion: str,
    ) -> int:
        """保存分析结果"""
        timestamp = datetime.now().isoformat()

        # 将复杂数据结构转换为JSON字符串
        similarity_matrix_json = json.dumps(similarity_matrix)
        consensus_scores_json = json.dumps(consensus_scores)
        key_points_json = json.dumps(key_points)
        differences_json = json.dumps(differences)

        # 类型断言：cursor和conn在_init_db中已初始化，不会为None
        cursor = cast(sqlite3.Cursor, self.cursor)
        conn = cast(sqlite3.Connection, self.conn)

        cursor.execute(
            "INSERT INTO analysis_results "
            "(session_id, similarity_matrix, consensus_scores, key_points, "
            "differences, comprehensive_summary, final_conclusion, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                similarity_matrix_json,
                consensus_scores_json,
                key_points_json,
                differences_json,
                comprehensive_summary,
                final_conclusion,
                timestamp,
            ),
        )
        conn.commit()
        # 类型断言确保返回int类型
        return cast(int, cursor.lastrowid)

    def get_analysis_result(self, session_id: int) -> Optional[AnalysisResultRecord]:
        """获取会话的分析结果"""
        # 类型断言：cursor在_init_db中已初始化，不会为None
        cursor = cast(sqlite3.Cursor, self.cursor)
        cursor.execute(
            "SELECT * FROM analysis_results WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        if row:
            return AnalysisResultRecord(
                id=row[0],
                session_id=row[1],
                similarity_matrix=json.loads(row[2]),
                consensus_scores=json.loads(row[3]),
                key_points=json.loads(row[4]),
                differences=json.loads(row[5]),
                comprehensive_summary=row[6],
                final_conclusion=row[7],
                timestamp=datetime.fromisoformat(row[8]),
            )
        return None

    def delete_session(self, session_id: int) -> None:
        """删除会话及其相关数据"""
        # 类型断言：cursor和conn在_init_db中已初始化，不会为None
        cursor = cast(sqlite3.Cursor, self.cursor)
        conn = cast(sqlite3.Connection, self.conn)

        cursor.execute(
            "DELETE FROM analysis_results WHERE session_id = ?", (session_id,)
        )
        cursor.execute("DELETE FROM tool_results WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()

    def clear_old_sessions(self, keep_count: int = 100) -> None:
        """清除旧会话，保留指定数量的最近会话"""
        # 类型断言：cursor和conn在_init_db中已初始化，不会为None
        cursor = cast(sqlite3.Cursor, self.cursor)
        conn = cast(sqlite3.Connection, self.conn)

        # 获取要保留的会话ID
        cursor.execute(
            "SELECT id FROM sessions ORDER BY timestamp DESC LIMIT ?", (keep_count,)
        )
        keep_ids = [row[0] for row in cursor.fetchall()]

        if keep_ids:
            # 删除不在保留列表中的会话
            placeholders = ",".join(["?"] * len(keep_ids))
            cursor.execute(
                f"DELETE FROM analysis_results "
                f"WHERE session_id NOT IN ({placeholders})",
                keep_ids,
            )
            cursor.execute(
                f"DELETE FROM tool_results WHERE session_id NOT IN ({placeholders})",
                keep_ids,
            )
            cursor.execute(
                f"DELETE FROM sessions WHERE id NOT IN ({placeholders})",
                keep_ids,
            )
            conn.commit()

    def __enter__(self) -> "DataManager":
        """上下文管理器入口"""
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """上下文管理器出口"""
        self.close()

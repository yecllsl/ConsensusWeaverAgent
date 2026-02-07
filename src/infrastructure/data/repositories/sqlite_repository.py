"""SQLite仓库实现

本模块实现了所有数据仓库接口，提供SQLite数据库的数据访问功能。
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, List, Optional

from src.infrastructure.data.data_validator import DataValidator
from src.infrastructure.data.repositories.interfaces import (
    IAnalysisResultRepository,
    ISessionRepository,
    IToolResultRepository,
)
from src.models.entities import AnalysisResult, Session, ToolResult


class SqliteSessionRepository(ISessionRepository):
    """SQLite会话仓库实现"""

    def __init__(self, connection: sqlite3.Connection, validator: DataValidator):
        self._conn = connection
        self._validator = validator

    async def get_by_id(self, id: int) -> Optional[Session]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row:
            return Session(
                id=row[0],
                original_question=row[1],
                refined_question=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                completed=bool(row[4]),
            )
        return None

    async def get_all(self) -> List[Session]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        return [
            Session(
                id=row[0],
                original_question=row[1],
                refined_question=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                completed=bool(row[4]),
            )
            for row in rows
        ]

    async def add(self, entity: Session) -> int:
        self._validator.validate_session(entity)
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO sessions "
            "(original_question, refined_question, timestamp, completed) "
            "VALUES (?, ?, ?, ?)",
            (
                entity.original_question,
                entity.refined_question,
                entity.timestamp.isoformat()
                if entity.timestamp
                else datetime.now().isoformat(),
                entity.completed,
            ),
        )
        result = cursor.lastrowid
        if result is None:
            result = 0
        return result

    async def add_batch(self, entities: List[Session]) -> List[int]:
        ids = []
        for entity in entities:
            id = await self.add(entity)
            ids.append(id)
        return ids

    async def update(self, entity: Session) -> None:
        self._validator.validate_session(entity)
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE sessions SET refined_question = ?, completed = ? WHERE id = ?",
            (entity.refined_question, entity.completed, entity.id),
        )

    async def delete(self, id: int) -> None:
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = ?", (id,))

    async def get_recent(self, limit: int = 10) -> List[Session]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM sessions ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        return [
            Session(
                id=row[0],
                original_question=row[1],
                refined_question=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                completed=bool(row[4]),
            )
            for row in rows
        ]

    async def get_by_question(self, question: str) -> Optional[Session]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM sessions WHERE original_question = ?", (question,)
        )
        row = cursor.fetchone()
        if row:
            return Session(
                id=row[0],
                original_question=row[1],
                refined_question=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                completed=bool(row[4]),
            )
        return None


class SqliteToolResultRepository(IToolResultRepository):
    """SQLite工具结果仓库实现"""

    def __init__(self, connection: sqlite3.Connection, validator: DataValidator):
        self._conn = connection
        self._validator = validator

    async def get_by_id(self, id: int) -> Optional[ToolResult]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM tool_results WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_entity(row)
        return None

    async def get_all(self) -> List[ToolResult]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM tool_results ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        return [self._row_to_entity(row) for row in rows]

    async def add(self, entity: ToolResult) -> int:
        self._validator.validate_tool_result(entity)
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO tool_results "
            "(session_id, tool_name, success, answer, "
            "error_message, execution_time, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                entity.session_id,
                entity.tool_name,
                entity.success,
                entity.answer,
                entity.error_message,
                entity.execution_time,
                entity.timestamp.isoformat()
                if entity.timestamp
                else datetime.now().isoformat(),
            ),
        )
        result = cursor.lastrowid
        if result is None:
            result = 0
        return result

    async def add_batch(self, entities: List[ToolResult]) -> List[int]:
        cursor = self._conn.cursor()
        ids = []
        for entity in entities:
            self._validator.validate_tool_result(entity)
            cursor.execute(
                "INSERT INTO tool_results "
                "(session_id, tool_name, success, answer, "
                "error_message, execution_time, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    entity.session_id,
                    entity.tool_name,
                    entity.success,
                    entity.answer,
                    entity.error_message,
                    entity.execution_time,
                    entity.timestamp.isoformat()
                    if entity.timestamp
                    else datetime.now().isoformat(),
                ),
            )
            lastrowid = cursor.lastrowid
            if lastrowid is None:
                lastrowid = 0
            ids.append(lastrowid)
        return ids

    async def update(self, entity: ToolResult) -> None:
        self._validator.validate_tool_result(entity)
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE tool_results SET "
            "success = ?, answer = ?, error_message = ?, execution_time = ? "
            "WHERE id = ?",
            (
                entity.success,
                entity.answer,
                entity.error_message,
                entity.execution_time,
                entity.id,
            ),
        )

    async def delete(self, id: int) -> None:
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM tool_results WHERE id = ?", (id,))

    async def get_by_session_id(self, session_id: int) -> List[ToolResult]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM tool_results WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )
        rows = cursor.fetchall()
        return [self._row_to_entity(row) for row in rows]

    async def save_batch_for_session(
        self, session_id: int, results: List[ToolResult]
    ) -> List[int]:
        cursor = self._conn.cursor()
        ids = []
        for result in results:
            result.session_id = session_id
            self._validator.validate_tool_result(result)
            cursor.execute(
                "INSERT INTO tool_results "
                "(session_id, tool_name, success, answer, "
                "error_message, execution_time, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    result.session_id,
                    result.tool_name,
                    result.success,
                    result.answer,
                    result.error_message,
                    result.execution_time,
                    result.timestamp.isoformat()
                    if result.timestamp
                    else datetime.now().isoformat(),
                ),
            )
            lastrowid = cursor.lastrowid
            if lastrowid is None:
                lastrowid = 0
            ids.append(lastrowid)
        return ids

    def _row_to_entity(self, row: Any) -> ToolResult:
        """将数据库行转换为实体"""
        return ToolResult(
            id=row[0],
            session_id=row[1],
            tool_name=row[2],
            success=bool(row[3]),
            answer=row[4],
            error_message=row[5],
            execution_time=row[6],
            timestamp=datetime.fromisoformat(row[7]),
        )


class SqliteAnalysisResultRepository(IAnalysisResultRepository):
    """SQLite分析结果仓库实现"""

    def __init__(self, connection: sqlite3.Connection, validator: DataValidator):
        self._conn = connection
        self._validator = validator

    async def get_by_id(self, id: int) -> Optional[AnalysisResult]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM analysis_results WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_entity(row)
        return None

    async def get_all(self) -> List[AnalysisResult]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM analysis_results ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        return [self._row_to_entity(row) for row in rows]

    async def add(self, entity: AnalysisResult) -> int:
        self._validator.validate_analysis_result(entity)
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO analysis_results "
            "(session_id, similarity_matrix, consensus_scores, key_points, "
            "differences, comprehensive_summary, final_conclusion, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entity.session_id,
                json.dumps(entity.similarity_matrix),
                json.dumps(entity.consensus_scores),
                json.dumps(entity.key_points),
                json.dumps(entity.differences),
                entity.comprehensive_summary,
                entity.final_conclusion,
                entity.timestamp.isoformat()
                if entity.timestamp
                else datetime.now().isoformat(),
            ),
        )
        result = cursor.lastrowid
        if result is None:
            result = 0
        return result

    async def add_batch(self, entities: List[AnalysisResult]) -> List[int]:
        ids = []
        for entity in entities:
            id = await self.add(entity)
            ids.append(id)
        return ids

    async def update(self, entity: AnalysisResult) -> None:
        self._validator.validate_analysis_result(entity)
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE analysis_results SET "
            "similarity_matrix = ?, consensus_scores = ?, key_points = ?, "
            "differences = ?, comprehensive_summary = ?, final_conclusion = ? "
            "WHERE id = ?",
            (
                json.dumps(entity.similarity_matrix),
                json.dumps(entity.consensus_scores),
                json.dumps(entity.key_points),
                json.dumps(entity.differences),
                entity.comprehensive_summary,
                entity.final_conclusion,
                entity.id,
            ),
        )

    async def delete(self, id: int) -> None:
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM analysis_results WHERE id = ?", (id,))

    async def get_by_session_id(self, session_id: int) -> Optional[AnalysisResult]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM analysis_results WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        if row:
            return self._row_to_entity(row)
        return None

    def _row_to_entity(self, row) -> AnalysisResult:
        """将数据库行转换为实体"""
        return AnalysisResult(
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

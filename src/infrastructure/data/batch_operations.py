"""批量操作接口

本模块实现了批量数据操作，用于提高数据访问性能。
"""

import sqlite3
from typing import Any, Dict, List


class BatchOperations:
    """批量操作类

    提供批量插入、更新和删除操作，减少数据库I/O次数。
    """

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    async def batch_insert_tool_results(
        self, results: List[Dict[str, Any]]
    ) -> List[int]:
        """批量插入工具结果"""
        cursor = self._conn.cursor()
        cursor.executemany(
            "INSERT INTO tool_results "
            "(session_id, tool_name, success, answer, "
            "error_message, execution_time, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    r["session_id"],
                    r["tool_name"],
                    r["success"],
                    r["answer"],
                    r["error_message"],
                    r["execution_time"],
                    r["timestamp"],
                )
                for r in results
            ],
        )
        last_rowid = cursor.lastrowid
        if last_rowid is not None:
            last_rowid = 0
        return [last_rowid - len(results) + i + 1 for i in range(len(results))]

    async def batch_update_sessions(self, updates: List[Dict[str, Any]]) -> None:
        """批量更新会话"""
        cursor = self._conn.cursor()
        for update in updates:
            set_clauses = []
            values = []

            if "refined_question" in update:
                set_clauses.append("refined_question = ?")
                values.append(update["refined_question"])

            if "completed" in update:
                set_clauses.append("completed = ?")
                values.append(update["completed"])

            if set_clauses:
                values.append(update["id"])
                query = f"UPDATE sessions SET {', '.join(set_clauses)} WHERE id = ?"
                cursor.execute(query, values)

    async def batch_delete_sessions(self, session_ids: List[int]) -> None:
        """批量删除会话"""
        cursor = self._conn.cursor()
        placeholders = ",".join(["?"] * len(session_ids))

        cursor.execute(
            f"DELETE FROM analysis_results WHERE session_id IN ({placeholders})",
            session_ids,
        )

        cursor.execute(
            f"DELETE FROM tool_results WHERE session_id IN ({placeholders})",
            session_ids,
        )

        cursor.execute(
            f"DELETE FROM sessions WHERE id IN ({placeholders})", session_ids
        )

    async def batch_insert_sessions(self, sessions: List[Dict[str, Any]]) -> List[int]:
        """批量插入会话"""
        cursor = self._conn.cursor()
        cursor.executemany(
            "INSERT INTO sessions "
            "(original_question, refined_question, timestamp, completed) "
            "VALUES (?, ?, ?, ?)",
            [
                (
                    s["original_question"],
                    s["refined_question"],
                    s["timestamp"],
                    s["completed"],
                )
                for s in sessions
            ],
        )
        last_rowid = cursor.lastrowid
        if last_rowid is not None:
            last_rowid = 0
        return [last_rowid - len(sessions) + i + 1 for i in range(len(sessions))]

    async def batch_insert_analysis_results(
        self, results: List[Dict[str, Any]]
    ) -> List[int]:
        """批量插入分析结果"""
        cursor = self._conn.cursor()
        cursor.executemany(
            "INSERT INTO analysis_results "
            "(session_id, similarity_matrix, consensus_scores, key_points, "
            "differences, comprehensive_summary, final_conclusion, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    r["session_id"],
                    r["similarity_matrix"],
                    r["consensus_scores"],
                    r["key_points"],
                    r["differences"],
                    r["comprehensive_summary"],
                    r["final_conclusion"],
                    r["timestamp"],
                )
                for r in results
            ],
        )
        last_rowid = cursor.lastrowid
        if last_rowid is not None:
            last_rowid = 0
        return [last_rowid - len(results) + i + 1 for i in range(len(results))]

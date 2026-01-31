import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from src.infrastructure.logging.logger import get_logger


class SortOrder(Enum):
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    CONSENSUS_DESC = "consensus_desc"
    CONSENSUS_ASC = "consensus_asc"


@dataclass
class SessionFilter:
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    keyword: Optional[str] = None
    min_consensus: Optional[float] = None
    max_consensus: Optional[float] = None
    limit: int = 20
    offset: int = 0
    sort_order: SortOrder = SortOrder.DATE_DESC


@dataclass
class SessionSummary:
    session_id: int
    question: str
    consensus_score: float
    created_at: datetime
    tool_count: int


@dataclass
class SessionDetails:
    session_id: int
    question: str
    refined_question: str
    tool_results: List[Dict[str, Any]]
    consensus_analysis: Dict[str, Any]
    report: str
    created_at: datetime


class HistoryManager:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.logger = get_logger()
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='sessions'
                """)
                if not cursor.fetchone():
                    return
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sessions_timestamp 
                    ON sessions(timestamp DESC)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sessions_completed 
                    ON sessions(completed)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tool_results_session_id 
                    ON tool_results(session_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analysis_results_session_id 
                    ON analysis_results(session_id)
                """)
                
                conn.commit()
                self.logger.info("数据库索引创建完成")
        except Exception as e:
            self.logger.error(f"创建数据库索引失败: {e}")

    def query_sessions(self, filters: SessionFilter) -> List[SessionSummary]:
        query = """
            SELECT
                s.id as session_id,
                s.original_question as question,
                s.timestamp as created_at,
                COUNT(tr.id) as tool_count,
                0.0 as consensus_score
            FROM sessions s
            LEFT JOIN tool_results tr ON s.id = tr.session_id
            WHERE s.completed = 1
        """
        params = []

        if filters.start_date:
            query += " AND s.timestamp >= ?"
            params.append(filters.start_date.isoformat())

        if filters.end_date:
            query += " AND s.timestamp <= ?"
            params.append(filters.end_date.isoformat())

        if filters.keyword:
            query += " AND (s.original_question LIKE ? OR s.refined_question LIKE ?)"
            keyword_pattern = f"%{filters.keyword}%"
            params.extend([keyword_pattern, keyword_pattern])

        query += " GROUP BY s.id"

        if filters.sort_order == SortOrder.DATE_DESC:
            query += " ORDER BY s.timestamp DESC"
        elif filters.sort_order == SortOrder.DATE_ASC:
            query += " ORDER BY s.timestamp ASC"
        elif filters.sort_order == SortOrder.CONSENSUS_DESC:
            query += " ORDER BY consensus_score DESC"
        elif filters.sort_order == SortOrder.CONSENSUS_ASC:
            query += " ORDER BY consensus_score ASC"

        query += " LIMIT ? OFFSET ?"
        params.extend([filters.limit, filters.offset])

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)

                results = []
                for row in cursor.fetchall():
                    results.append(SessionSummary(
                        session_id=row["session_id"],
                        question=row["question"],
                        consensus_score=row["consensus_score"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        tool_count=row["tool_count"]
                    ))

                self.logger.info(f"查询到 {len(results)} 条历史记录")
                return results
        except Exception as e:
            self.logger.error(f"查询历史记录失败: {e}")
            raise

    def get_session_details(self, session_id: int) -> Optional[SessionDetails]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id as session_id, original_question as question, refined_question, timestamp as created_at
                    FROM sessions
                    WHERE id = ?
                """, (session_id,))

                session_row = cursor.fetchone()
                if not session_row:
                    return None

                cursor.execute("""
                    SELECT tool_name, success, answer, error_message, execution_time, timestamp
                    FROM tool_results
                    WHERE session_id = ?
                """, (session_id,))

                tool_results = []
                for row in cursor.fetchall():
                    tool_results.append({
                        "tool_name": row["tool_name"],
                        "success": bool(row["success"]),
                        "answer": row["answer"],
                        "error_message": row["error_message"],
                        "execution_time": row["execution_time"],
                        "timestamp": row["timestamp"]
                    })

                cursor.execute("""
                    SELECT similarity_matrix, consensus_scores, key_points, differences, final_conclusion
                    FROM analysis_results
                    WHERE session_id = ?
                """, (session_id,))

                analysis_row = cursor.fetchone()
                consensus_analysis = {}
                if analysis_row:
                    consensus_analysis = {
                        "similarity_matrix": json.loads(analysis_row["similarity_matrix"]),
                        "consensus_scores": json.loads(analysis_row["consensus_scores"]),
                        "key_points": json.loads(analysis_row["key_points"]),
                        "differences": json.loads(analysis_row["differences"]),
                        "final_recommendation": analysis_row["final_conclusion"]
                    }

                report = ""

                return SessionDetails(
                    session_id=session_row["session_id"],
                    question=session_row["question"],
                    refined_question=session_row["refined_question"] or "",
                    tool_results=tool_results,
                    consensus_analysis=consensus_analysis,
                    report=report,
                    created_at=datetime.fromisoformat(session_row["created_at"])
                )
        except Exception as e:
            self.logger.error(f"获取会话详情失败: {e}")
            raise

    def export_sessions(
        self,
        sessions: List[SessionSummary],
        format: str = "json",
        output_path: str = "history_export.json"
    ) -> None:
        try:
            if format == "json":
                data = [
                    {
                        "session_id": s.session_id,
                        "question": s.question,
                        "consensus_score": s.consensus_score,
                        "created_at": s.created_at.isoformat(),
                        "tool_count": s.tool_count
                    }
                    for s in sessions
                ]
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif format == "csv":
                import csv
                with open(output_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["session_id", "question", "consensus_score", "created_at", "tool_count"])
                    for s in sessions:
                        writer.writerow([
                            s.session_id,
                            s.question,
                            s.consensus_score,
                            s.created_at.isoformat(),
                            s.tool_count
                        ])
            else:
                raise ValueError(f"不支持的导出格式: {format}")

            self.logger.info(f"历史记录已导出到: {output_path}")
        except Exception as e:
            self.logger.error(f"导出历史记录失败: {e}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM sessions WHERE completed = 1")
                total_sessions = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(DISTINCT tool_name) FROM tool_results")
                unique_tools = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM tool_results")
                total_tool_executions = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM tool_results WHERE success = 1")
                successful_executions = cursor.fetchone()[0]

                return {
                    "total_sessions": total_sessions,
                    "average_consensus_score": 0.0,
                    "unique_tools_used": unique_tools,
                    "total_tool_executions": total_tool_executions,
                    "successful_executions": successful_executions,
                    "success_rate": successful_executions / total_tool_executions if total_tool_executions > 0 else 0.0
                }
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            raise

    def search_by_keyword(self, keyword: str, limit: int = 10) -> List[SessionSummary]:
        filters = SessionFilter(keyword=keyword, limit=limit)
        return self.query_sessions(filters)

    def filter_by_consensus(
        self,
        min_score: float,
        max_score: Optional[float] = None,
        limit: int = 10
    ) -> List[SessionSummary]:
        filters = SessionFilter(
            min_consensus=min_score,
            max_consensus=max_score,
            limit=limit,
            sort_order=SortOrder.CONSENSUS_DESC
        )
        return self.query_sessions(filters)

    def get_recent_sessions(self, limit: int = 10) -> List[SessionSummary]:
        filters = SessionFilter(limit=limit, sort_order=SortOrder.DATE_DESC)
        return self.query_sessions(filters)

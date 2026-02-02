import csv
import json
import os
import sqlite3
import tempfile
from datetime import datetime

import pytest

from src.service.history.history_manager import (
    HistoryManager,
    SessionDetails,
    SessionFilter,
    SessionSummary,
    SortOrder,
)


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
        except Exception:
            pass


@pytest.fixture
def history_manager(temp_db):
    return HistoryManager(temp_db)


@pytest.fixture
def populated_db(temp_db):
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_question TEXT NOT NULL,
                refined_question TEXT,
                timestamp TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE
            )
        """)

        cursor.execute("""
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

        cursor.execute("""
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

        cursor.execute(
            """
            INSERT INTO sessions (original_question, completed, timestamp)
            VALUES (?, 1, ?)
        """,
            ("测试问题1", datetime.now().isoformat()),
        )
        session_id1 = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO sessions (original_question, completed, timestamp)
            VALUES (?, 1, ?)
        """,
            ("测试问题2", datetime.now().isoformat()),
        )

        cursor.execute(
            """
            INSERT INTO tool_results (session_id, tool_name, success, answer,
                                     error_message, execution_time, timestamp)
            VALUES (?, 'tool1', 1, '答案1', NULL, 1.0, ?)
        """,
            (session_id1, datetime.now().isoformat()),
        )

        cursor.execute(
            """
            INSERT INTO analysis_results (
                session_id, similarity_matrix, consensus_scores,
                key_points, differences, comprehensive_summary,
                final_conclusion, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id1,
                json.dumps([[1.0, 0.8], [0.8, 1.0]]),
                json.dumps({"tool1": 0.9}),
                json.dumps([{"content": "观点1", "sources": "tool1"}]),
                json.dumps([]),
                "综合总结",
                "最终结论",
                datetime.now().isoformat(),
            ),
        )

        conn.commit()

    return temp_db


@pytest.fixture
def populated_history_manager(populated_db):
    return HistoryManager(populated_db)


def test_history_manager_initialization(history_manager, temp_db):
    assert history_manager.db_path == temp_db


def test_query_sessions_empty(populated_history_manager):
    filters = SessionFilter(keyword="不存在的问题")
    results = populated_history_manager.query_sessions(filters)

    assert results == []


def test_query_sessions_with_data(populated_histo@pytest.mark.unit
ry_manager):
    filters = SessionFilter()
    results = populated_history_manager.query_sessions@pytest.mark.unit
(filters)

    assert len(results) == 2
    assert all(isinstance(r, SessionSummary) for r in results)


def test_query_sessions_with_keyword(populated_history_manager):
    filt@pytest.mark.unit
ers = SessionFilter(keyword="测试问题1")
    results = populated_history_manager.query_sessions(filters)

    assert len(results) == 1
    assert "测试问题1" in results[0].question


def test_query_sessions_with_consensus_filter(populated_hi@pytest.mark.unit
story_manager):
    filters = SessionFilter(min_consensus=0.0, max_consensus=1.0)
    results = populated_history_manager.query_sessions(filters)

    assert len(results) >= 1


def test_query_sessions_with_limit(populated_history@pytest.mark.unit
_manager):
    filters = SessionFilter(limit=1)
    results = populated_history_manager.query_sessions(filters)

    assert len(results) == 1


def test_query_sessions_with_sort_order(populated_history_manager):
    fi@pytest.mark.unit
lters = SessionFilter(sort_order=SortOrder.DATE_DESC)
    results = populated_history_manager.query_sessions(filters)

    assert len(results) == 2


def test_get_session_details@pytest.mark.unit
_not_found(populated_history_manager):
    details = populated_history_manager.get_session_details(999)

    assert details is None


def test_get_session_details_found(populated_history_manager):
    detai@pytest.mark.unit
ls = populated_history_manager.get_session_details(1)

    assert details is not None
    assert isinstance(details, SessionDetails)
    assert @pytest.mark.unit
details.session_id == 1
    assert details.question == "测试问题1"


def test_export_sessions_json(populated_history_manager, tmp_path):
    sessions = [
        SessionSummary(
            session_id=1,
            question="问题1",
            consensus_score=0.9,
  @pytest.mark.unit
          created_at=datetime.now(),
            tool_count=2,
        )
    ]

    output_path = os.path.join(str(tmp_path), "export.json")
    populated_history_manager.export_sessions(
        sessions, format="json", output_path=str(output_path)
    )

    assert os.path.exists(output_path)

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["question"] == "问题1"


def test_export_sessions_csv(populated_history_manager, tmp_path):
    sessions = [
        SessionSummary(
            session_id=1,
            question="问题1",
            consen@pytest.mark.unit
sus_score=0.9,
            created_at=datetime.now(),
            tool_count=2,
        )
    ]

    output_path = os.path.join(str(tmp_path), "export.csv")
    populated_history_manager.export_sessions(
        sessions, format="csv", output_path=str(output_path)
    )

    assert os.path.exists(output_path)

    with open(output_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0] == [
        "session_id",
        "question",
        "consensus_score",
        "created_at",
        "tool_count",
    ]


def test_export_sessions_unsupported_format(populated_history_manager, tmp_path):
    sessions = []

    output_path = os.path.join(str(tmp_path), "export.txt")

@pytest.mark.unit
    with pytest.raises(ValueError):
        populated_history_manager.export_sessions(
            sessions, format="txt", output_path=str(output_path)
        )


def test_get_statistics(populated_history_manager):
    stats = populated_history_manager.get_statistics()

    assert isinstance(stats, dict)
 @pytest.mark.unit
   assert "total_sessions" in stats
    assert "average_consensus_score" in stats
    assert "unique_tools_used" in stats
    assert "total_tool_executions" in stats
    assert "successful_executions" in stats
    assert "success_rate" in stats


def test_search_by_keyword(populated_history_manager):
    results = populated_history_manager.search_by_keyword("测试", limit=1@pytest.mark.unit
0)

    assert len(results) >= 1
    assert all("测试" in r.question for r in results)


def test_filter_by_consensus(populated_history_manager):
    results = populated_history_manager.filter_by_c@pytest.mark.unit
onsensus(
        0.0, max_score=1.0, limit=10
    )

    assert isinstance(results, list)


def test_filter_by_consensus_no_max(populated_history_manager):
    results = populated_hi@pytest.mark.unit
story_manager.filter_by_consensus(0.0, limit=10)

    assert isinstance(results, list)


def test_get_recent_sessions(populated_history_manager):
    results = p@pytest.mark.unit
opulated_history_manager.get_recent_sessions(limit=10)

    assert len(results) >= 1


def test_session_filter_defaults():
    filters = Sess@pytest.mark.unit
ionFilter()

    assert filters.start_date is None
    assert filters.end_date is None
    assert filters.keyword is None
    assert filters.min_consensus is None
    assert filters.max_consensus is None
    assert filters.limit == 20
    assert filters.offset == 0
    assert filters.sort_order == SortOrder.DATE_DESC


def test_session_summary_creation():@pytest.mark.unit

    summary = SessionSummary(
        session_id=1,
        question="测试问题",
        consensus_score=0.9,
        created_at=datetime.now(),
        tool_count=2,
    )

    assert summary.session_id == 1
    assert summary.question == "测试问题"
    assert summary.consensus_score == 0.9
    assert summary.tool_count == 2


def test_session_d@pytest.mark.unit
etails_creation():
    details = SessionDetails(
        session_id=1,
        question="问题",
        refined_question="重构问题",
        tool_results=[],
        consensus_analysis={},
        report="报告",
        created_at=datetime.now(),
    )

    assert details.session_id == 1
    assert details.question == "问题"
    assert details.refined_question == "重构问题"
    assert details.report == "报告"


@pytest.mark.unit
def test_ensure_indexes(populated_history_manager):
    with sqlite3.connect(populated_history_manager.db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
        """)

        indexes = [row[0] for row in cursor.fetchall()]

        assert "idx_sessions_timestamp" in indexes
        assert "idx_sessions_completed" in indexes
        assert "idx_tool_results_session_id" in indexes
        assert "idx_analysis_results_session_id" in indexes

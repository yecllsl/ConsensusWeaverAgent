import pytest
from src.infrastructure.data.data_manager import (
    AnalysisResultRecord,
    DataManager,
    SessionRecord,
)


# 测试数据管理器的基本功能
@pytest.mark.unit
@pytest.mark.database
def test_data_manager_basic(data_manager, test_data):
        # 测试保存会话
        original_question = test_data["original_question"]
        session_id = data_manager.save_session(original_question)

        # 测试获取会话
        session = data_manager.get_session(session_id)
        assert isinstance(session, SessionRecord)
        assert session.original_question == original_question
        assert not session.completed

        # 测试更新会话
        refined_question = test_data["refined_question"]
        data_manager.update_session(
            session_id, refined_question=refined_question, completed=True
        )

        # 验证会话更新
        updated_session = data_manager.get_session(session_id)
        assert updated_session.refined_question == refined_question
        assert updated_session.completed

        # 测试保存工具结果
        data_manager.save_tool_result(
            session_id=session_id,
            tool_name="iflow",
            success=True,
            answer="人工智能是...",
            error_message="",
            execution_time=1.5,
        )

        # 测试获取工具结果
        tool_results = data_manager.get_tool_results(session_id)
        assert len(tool_results) == 1
        assert tool_results[0].tool_name == "iflow"
        assert tool_results[0].success
        assert tool_results[0].answer == "人工智能是..."

        # 测试保存分析结果
        similarity_matrix = test_data["similarity_matrix"]
        consensus_scores = test_data["consensus_scores"]
        key_points = test_data["key_points"]
        differences = test_data["differences"]
        comprehensive_summary = test_data["comprehensive_summary"]
        final_conclusion = test_data["final_conclusion"]

        data_manager.save_analysis_result(
            session_id=session_id,
            similarity_matrix=similarity_matrix,
            consensus_scores=consensus_scores,
            key_points=key_points,
            differences=differences,
            comprehensive_summary=comprehensive_summary,
            final_conclusion=final_conclusion,
        )

        # 测试获取分析结果
        analysis_result = data_manager.get_analysis_result(session_id)
        assert isinstance(analysis_result, AnalysisResultRecord)
        assert analysis_result.similarity_matrix == similarity_matrix
        assert analysis_result.consensus_scores == consensus_scores
        assert analysis_result.key_points == key_points
        assert analysis_result.differences == differences
        assert analysis_result.comprehensive_summary == comprehensive_summary
        assert analysis_result.final_conclusion == final_conclusion


# 测试会话管理功能
@pytest.mark.unit
@pytest.mark.database
def test_session_management(data_manager):
        # 创建多个会话
        session_ids = []
        for i in range(5):
            session_id = data_manager.save_session(f"问题 {i}")
            session_ids.append(session_id)

        # 测试获取最近会话
        recent_sessions = data_manager.get_recent_sessions(limit=3)
        assert len(recent_sessions) == 3

        # 测试删除会话
        data_manager.delete_session(session_ids[0])
        deleted_session = data_manager.get_session(session_ids[0])
        assert deleted_session is None

        # 测试清除旧会话
        data_manager.clear_old_sessions(keep_count=2)
        recent_sessions_after_clear = data_manager.get_recent_sessions(limit=10)
        assert len(recent_sessions_after_clear) == 2


# 测试异常情况
def test_data_manager_exceptions(tmp_path):
    db_path = tmp_path / "test_exceptions.db"

    with DataManager(str(db_path)) as data_manager:
        # 测试获取不存在的会话
        non_existent_session = data_manager.get_session(999)
        assert non_existent_session is None

        # 测试获取不存在会话的工具结果
        tool_results = data_manager.get_tool_results(999)
        assert len(tool_results) == 0

        # 测试获取不存在会话的分析结果
        analysis_result = data_manager.get_analysis_result(999)
        assert analysis_result is None

        # 测试删除不存在的会话（应该不会抛出异常）
        data_manager.delete_session(999)

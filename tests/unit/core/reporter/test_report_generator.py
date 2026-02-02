from datetime import datetime
from unittest.mock import Mock

import pytest

from src.core.reporter.report_generator import Report, ReportGenerator


@pytest.fixture
def mock_data_manager():
    data_manager = Mock()
    return data_manager


@pytest.fixture
def report_generator(mock_data_manager):
    return ReportGenerator(mock_data_manager)


@pytest.fixture
def mock_session():
    session = Mock()
    session.id = 1
    session.original_question = "测试问题"
    session.refined_question = "重构问题"
    return session


@pytest.fixture
def mock_tool_results():
    result1 = Mock()
    result1.tool_name = "tool1"
    result1.success = True
    result1.answer = "答案1"
    result1.error_message = None
    result1.execution_time = 1.0
    result1.timestamp = datetime.now()

    result2 = Mock()
    result2.tool_name = "tool2"
    result2.success = True
    result2.answer = "答案2"
    result2.error_message = None
    result2.execution_time = 1.0
    result2.timestamp = datetime.now()

    return [result1, result2]


@pytest.fixture
def mock_analysis():
    analysis = Mock()
    analysis.similarity_matrix = [[1.0, 0.8], [0.8, 1.0]]
    analysis.consensus_scores = {"tool1": 0.9, "tool2": 0.85}
    analysis.key_points = [{"content": "观点1", "sources": "tool1,tool2"}]
    analysis.differences = [{"content": "分歧1", "sources": "tool1"}]
    analysis.comprehensive_summary = "综合总结"
    analysis.final_conclusion = "最终结论"
    return analysis


def test_generate_report_success(
    report_generator, mock_data_manager, mock_session, mock_tool_results, mock_analysis
):
    session_id = 1

    mock_data_manager.get_session.return_value = mock_session
    mock_data_manager.get_tool_results.return_value = mock_tool_results
    mock_data_manager.get_analysis_result.return_value = mock_analysis

    report = report_generator.generate_report(session_id)

    assert report.session_id == session_id
    assert report.original_question == "测试问题"
    assert report.refined_question == "重构问题"
    assert len(report.tool_results) == 2
    assert report.comprehensive_summary == "综合总结"
    assert report.final_conclusion == "最终结论"
    assert "# 智能问答协调终端" in report.content


def test_generate_report_session_not_found(report_generator, mock_data_manager):
    session_id = 999

    mock_data_manager.get_session.return_value = None

    with pytest.raises(ValueError, match="不存在"):
        report_generator.generate_report(session_id)


def test_generate_report_analysis_not_found(
    report_generator, mock_data_manager, mock_session, mock_tool_results
):
    session_id = 1

    mock_data_manager.get_session.return_value = mock_session
    mock_data_manager.get_tool_results.return_value = mock_tool_results
    mock_data_manager.get_analysis_result.return_value = None

    with pytest.raises(ValueError, match="没有分析结果"):
        report_generator.generate_report(session_id)


def test_render_text_report(
    report_generator, mock_session, mock_tool_results, mock_analysis
):
    content = report_generator._render_text_report(
        mock_session, mock_tool_results, mock_analysis
    )

    assert "# 智能问答协调终端" in content
    assert "测试问题" in content
    assert "重构问题" in content
    assert "tool1" in content
    assert "tool2" in content
    assert "综合总结" in content
    assert "最终结论" in content


def test_render_text_report_no_refined_question(
    report_generator, mock_tool_results, mock_analysis
):
    mock_session = Mock()
    mock_session.id = 1
    mock_session.original_question = "测试问题"
    mock_session.refined_question = None

    content = report_generator._render_text_report(
        mock_session, mock_tool_results, mock_analysis
    )

    assert "测试问题" in content
    assert "重构问题" not in content


def test_render_text_report_failed_tool(report_generator, mock_session, mock_analysis):
    failed_result = Mock()
    failed_result.tool_name = "failed_tool"
    failed_result.success = False
    failed_result.answer = None
    failed_result.error_message = "错误信息"
    failed_result.execution_time = 1.0
    failed_result.timestamp = datetime.now()

    content = report_generator._render_text_report(
        mock_session, [failed_result], mock_analysis
    )

    assert "失败" in content
    assert "错误信息" in content


def test_render_text_report_no_differences(
    report_generator, mock_session, mock_tool_results
):
    mock_analysis = Mock()
    mock_analysis.similarity_matrix = [[1.0]]
    mock_analysis.consensus_scores = {"tool1": 1.0}
    mock_analysis.key_points = []
    mock_analysis.differences = []
    mock_analysis.comprehensive_summary = "综合总结"
    mock_analysis.final_conclusion = "最终结论"

    content = report_generator._render_text_report(
        mock_session, mock_tool_results, mock_analysis
    )

    assert "无明显分歧" in content


def test_save_report_with_path(report_generator, tmp_path):
    report = Report(
        session_id=1,
        original_question="测试问题",
        refined_question="重构问题",
        generated_at=datetime.now(),
        tool_results=[],
        consensus_analysis={},
        comprehensive_summary="总结",
        final_conclusion="结论",
        content="报告内容",
    )

    file_path = tmp_path / "test_report.txt"
    saved_path = report_generator.save_report(report, str(file_path))

    assert saved_path == str(file_path)
    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == "报告内容"


def test_save_report_without_path(report_generator):
    report = Report(
        session_id=1,
        original_question="测试问题",
        refined_question="重构问题",
        generated_at=datetime.now(),
        tool_results=[],
        consensus_analysis={},
        comprehensive_summary="总结",
        final_conclusion="结论",
        content="报告内容",
    )

    saved_path = report_generator.save_report(report)

    assert saved_path.startswith("reports/report_1_")
    assert saved_path.endswith(".txt")


def test_get_report_content_success(
    report_generator, mock_data_manager, mock_session, mock_tool_results, mock_analysis
):
    session_id = 1

    mock_data_manager.get_session.return_value = mock_session
    mock_data_manager.get_tool_results.return_value = mock_tool_results
    mock_data_manager.get_analysis_result.return_value = mock_analysis

    content = report_generator.get_report_content(session_id)

    assert content is not None
    assert "# 智能问答协调终端" in content


def test_get_report_content_failure(report_generator, mock_data_manager):
    session_id = 999

    mock_data_manager.get_session.return_value = None

    content = report_generator.get_report_content(session_id)

    assert content is None


def test_export_report_text_format(
    report_generator, mock_data_manager, mock_session, mock_tool_results, mock_analysis
):
    session_id = 1

    mock_data_manager.get_session.return_value = mock_session
    mock_data_manager.get_tool_results.return_value = mock_tool_results
    mock_data_manager.get_analysis_result.return_value = mock_analysis

    file_path = report_generator.export_report(session_id, format="text")

    assert file_path.startswith("reports/report_1_")


@pytest.mark.unit
def test_export_report_unsupported_format(report_generator):
    session_id = 1

    with pytest.raises(ValueError, match="不支持的报告格式"):
        report_generator.export_report(session_id, format="unsupported")

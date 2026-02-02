import json
import os
from datetime import datetime
from unittest.mock import Mock

import pytest

from src.core.reporter.multi_format_reporter import MultiFormatReporter, ReportFormat
from src.infrastructure.data.data_manager import (
    AnalysisResultRecord,
    SessionRecord,
    ToolResultRecord,
)


@pytest.fixture
def mock_data_manager():
    data_manager = Mock()

    session = SessionRecord(
        id=1,
        original_question="测试问题",
        refined_question="重构后的测试问题",
        timestamp=datetime.now(),
        completed=True,
    )

    tool_results = [
        ToolResultRecord(
            id=1,
            session_id=1,
            tool_name="test_tool1",
            success=True,
            answer="这是测试工具1的回答",
            error_message=None,
            execution_time=1.5,
            timestamp=datetime.now(),
        ),
        ToolResultRecord(
            id=2,
            session_id=1,
            tool_name="test_tool2",
            success=True,
            answer="这是测试工具2的回答",
            error_message=None,
            execution_time=2.0,
            timestamp=datetime.now(),
        ),
    ]

    analysis = AnalysisResultRecord(
        id=1,
        session_id=1,
        similarity_matrix=[[1.0, 0.8], [0.8, 1.0]],
        consensus_scores={"test_tool1": 0.9, "test_tool2": 0.85},
        key_points=[
            {"content": "核心观点1", "sources": "test_tool1"},
            {"content": "核心观点2", "sources": "test_tool2"},
        ],
        differences=[],
        comprehensive_summary="这是一个综合总结",
        final_conclusion="这是最终结论",
        timestamp=datetime.now(),
    )

    data_manager.get_session.return_value = session
    data_manager.get_tool_results.return_value = tool_results
    data_manager.get_analysis_result.return_value = analysis

    return data_manager


@pytest.fixture
def multi_format_reporter(mock_data_manager):
    return MultiFormatReporter(mock_data_manager)


def test_multi_format_reporter_initialization(multi_format_reporter, mock_data_manager):
    assert multi_format_reporter.data_manager == mock_data_manager


def test_generate_text_report(multi_format_reporter):
    report = multi_format_reporter.generate_report(1, ReportFormat.TEXT)

    assert report.session_id == 1
    assert report.original_question == "@pytest.mark.unit
测试问题"
    assert "智能问答协调终端 - 分析报告" in report.content
    assert "测试问题" in report.content
    assert "test_tool1" in report.content
    asser@pytest.mark.unit
t "test_tool2" in report.content


def test_generate_markdown_report(multi_format_reporter):
    report = multi_format_reporter.generate_report(1, ReportFormat.MARKDOWN)

    assert report.session_id == 1
    assert report.original_question == "测试问题"
    assert "# 智能问答协调终端 - 分析报告" in report.content
    assert "## 1. 基本信息" in report.content
    assert "## 2.@pytest.mark.unit
 问题描述" in report.content
    assert "## 3. 工具结果" in report.content
    assert "## 4. 共识分析" in report.content
    assert "## 5. 综合总结" in report.content
    assert "## 6. 最终结论" in report.content


def test_generate_html_report(multi_format_reporter):
    report = multi_format_reporter.generate_report(1, ReportFormat.HTML)

    assert report.session_id == 1
    assert report.original_question == "测试问题"
    assert "<!DOCTYPE html>" in report.content
    assert "<html lang='zh-CN'>" in report.content
@pytest.mark.unit
    assert "<title>智能问答协调终端 - 分析报告</title>" in report.content
    assert "测试问题" in report.content
    assert "test_tool1" in report.content
    assert "test_tool2" in report.content


def test_generate_json_report(multi_format_reporter):
    report = multi_format_reporter.generate_report(1, ReportFormat.JSON)

    assert report.session_id == 1
    assert report.original_question == "测试问题"

    report_data = json.loads(report.content)
    assert report_data["session_id@pytest.mark.unit
"] == 1
    assert report_data["original_question"] == "测试问题"
    assert report_data["refined_question"] == "重构后的测试问题"
    assert len(report_data["tool_results"]) == 2
    assert report_data["consensus_analysis"]["consensus_scores"]["test_tool1"] == 0.9
    assert report_data["comprehensive_summary"] == "这是一个综合总结"
    assert report_data["final_conclusion"] == "这是最终结论"


def test_generate_pdf_report(multi_format_reporter):
    report = multi_format_reporter.generate_report(1, ReportFormat.PDF)

    assert report.session_id == 1
    assert report.original_question == "测试问题"
    assert isinstance(report.content, (str, bytes))


def test_g@pytest.mark.unit
enerate_unsupported_format(multi_format_reporter):
    with pytest.raises(ValueError, match="不支持的报告格式"):
        multi_format_reporter.generate_report(1, "unsupported_format")


def test_save_text_report(multi_format_reporter, tmp_path):
    @pytest.mark.unit
report = multi_format_reporter.generate_report(1, ReportFormat.TEXT)

    file_path = os.path.join(str(tmp_path), "test_report.txt")
    saved_path = multi_format_reporte@pytest.mark.unit
r.save_report(report, file_path, ReportFormat.TEXT)

    assert saved_path == file_path
    assert os.path.exists(file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "智能问答协调终端 - 分析报告" in content


def test_save_markdown_report(multi_format_reporter, tmp_path):
    report = multi_format_reporter.generate_report(1, ReportFormat.MARKDOWN)

    file_path = os.path.join(str(tmp_path), "test_report.md")
    saved_pa@pytest.mark.unit
th = multi_format_reporter.save_report(
        report, file_path, ReportFormat.MARKDOWN
    )

    assert saved_path == file_path
    assert os.path.exists(file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# 智能问答协调终端 - 分析报告" in content


def test_save_html_report(multi_format_reporter, tmp_path):
    report = multi_format_reporter.generate_report(1, ReportFormat.HTML)

    file_path = os.path.join(str(tmp_path), "test_report.html")
@pytest.mark.unit
    saved_path = multi_format_reporter.save_report(report, file_path, ReportFormat.HTML)

    assert saved_path == file_path
    assert os.path.exists(file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "<!DOCTYPE html>" in content


def test_save_json_report(multi_format_reporter, tmp_path):
    report = multi_format_reporter.generate_report(1, ReportFormat.JSON)

    file_path = os.path.join(str(tmp_path), "t@pytest.mark.unit
est_report.json")
    saved_path = multi_format_reporter.save_report(report, file_path, ReportFormat.JSON)

    assert saved_path == file_path
    assert os.path.exists(file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    data = json.loads(content)
    assert data["session_id"] == 1


def test_save_pdf_report(multi_format_reporter, tmp_path):
    report = multi_format_reporter.generate_report(1, ReportFormat.PDF)

    file_path = os.path.join(s@pytest.mark.unit
tr(tmp_path), "test_report.pdf")
    saved_path = multi_format_reporter.save_report(report, file_path, ReportFormat.PDF)

    assert saved_path == file_path
    assert os.path.exists(file_path)


def test_save_report_auto_filename(multi_format_reporter):
    report = multi_format_reporter.generate_report(1, ReportFormat.TEXT)

    saved_p@pytest.mark.unit
ath = multi_format_reporter.save_report(report, format=ReportFormat.TEXT)

    assert os.path.exists(saved_path)
    assert saved_path.startswith("reports/report_1_")
    assert saved_path.endswith(".txt")

    os.unlink(saved_path)


def test_export_report(multi_format_reporter, tmp_path):
    file_path = os.path.join(str(tmp_path), "exported_report.txt")
  @pytest.mark.unit
  saved_path = multi_format_reporter.export_report(1, ReportFormat.TEXT, file_path)

    assert saved_path == file_path
    assert os.path.exists(file_path)


def test_get_supported_formats(multi_format_reporter):
    formats = multi_format_reporter.get_supported_for@pytest.mark.unit
mats()

    assert ReportFormat.TEXT in formats
    assert ReportFormat.MARKDOWN in formats
    assert ReportFormat.HTML in formats
    assert ReportFormat.JSON in formats
    assert ReportFormat.PDF in formats
    assert len(formats) == 5


def test_generate_report_session_not_found(mock_data_manager):
    mock_data_manager.get_s@pytest.mark.unit
ession.return_value = None
    reporter = MultiFormatReporter(mock_data_manager)

    with pytest.raises(ValueError, match="会话 1 不存在"):
        reporter.generate_report(1, ReportFormat.TEXT)


def test_generate_report_no_analysis_result(mock_data_manager):
    mock@pytest.mark.unit
_data_manager.get_analysis_result.return_value = None
    reporter = MultiFormatReporter(mock_data_manager)

    with pytest.raises(ValueError, match="会话 1 没有分析结果"):
        reporter.generate_report(1, ReportFormat.TEXT)


def test_markdown_report_contains_tool_details(multi_f@pytest.mark.unit
ormat_reporter):
    report = multi_format_reporter.generate_report(1, ReportFormat.MARKDOWN)

    assert "### test_tool1" in report.content
    assert "### test_tool2" in report.content
    assert "✅ 成功" in report.content
    assert "这是测试工具1的回答" in report.content
    assert "这是测试工具2的回答" in report.content


def test_html_report_contains_stylin@pytest.mark.unit
g(multi_format_reporter):
    report = multi_format_reporter.generate_report(1, ReportFormat.HTML)

    assert "<style>" in report.content
    assert "body {" in report.content
    assert "h1 {" in report.content
    assert "table {" in report.content
    assert "</style>" in report.content


def test_json_repo@pytest.mark.unit
rt_structure(multi_format_reporter):
    report = multi_format_reporter.generate_report(1, ReportFormat.JSON)
    data = json.loads(report.content)

    assert "session_id" in data
    assert "original_question" in data
    assert "refined_question" in data
    assert "generated_at" in data
    assert "tool_results" in data
    assert "consensus_analysis" in data
    assert "comprehensive_summary" in data
    assert "final_conclusion" in data


@pytest.mark.unit
def test_text_report_contains_all_sections(multi_format_reporter):
    report = multi_format_reporter.generate_report(1, ReportFormat.TEXT)

    assert "# 智能问答协调终端 - 分析报告" in report.content
    assert "## 1. 基本信息" in report.content
    assert "## 2. 问题描述" in report.content
    assert "## 3. 工具结果" in report.content
    assert "## 4. 共识分析" in report.content
    assert "### 相似度矩阵" in report.content
    assert "### 共识度评分" in report.content
    assert "### 核心观点" in report.content
    assert "### 分歧点" in report.content
    assert "## 5. 综合总结" in report.content
    assert "## 6. 最终结论" in report.content

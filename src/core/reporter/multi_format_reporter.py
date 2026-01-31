import json
import os
from datetime import datetime
from typing import List, Optional

from src.core.reporter.report_generator import Report
from src.infrastructure.data.data_manager import (
    AnalysisResultRecord,
    DataManager,
    SessionRecord,
    ToolResultRecord,
)
from src.infrastructure.logging.logger import get_logger


class ReportFormat:
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    PDF = "pdf"


class MultiFormatReporter:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.logger = get_logger()

    def generate_report(
        self, session_id: int, format: str = ReportFormat.TEXT
    ) -> Report:
        self.logger.info(f"开始生成{format}格式报告，会话ID: {session_id}")

        try:
            session = self.data_manager.get_session(session_id)
            if not session:
                self.logger.error(f"会话 {session_id} 不存在")
                raise ValueError(f"会话 {session_id} 不存在")

            tool_results = self.data_manager.get_tool_results(session_id)
            tool_results_dict = [
                {
                    "tool_name": result.tool_name,
                    "success": result.success,
                    "answer": result.answer,
                    "error_message": result.error_message,
                    "execution_time": result.execution_time,
                    "timestamp": result.timestamp.isoformat(),
                }
                for result in tool_results
            ]

            analysis = self.data_manager.get_analysis_result(session_id)
            if not analysis:
                self.logger.error(f"会话 {session_id} 没有分析结果")
                raise ValueError(f"会话 {session_id} 没有分析结果")

            consensus_analysis = {
                "similarity_matrix": analysis.similarity_matrix,
                "consensus_scores": analysis.consensus_scores,
                "key_points": analysis.key_points,
                "differences": analysis.differences,
            }

            if format == ReportFormat.TEXT:
                content = self._render_text_report(session, tool_results, analysis)
            elif format == ReportFormat.MARKDOWN:
                content = self._render_markdown_report(session, tool_results, analysis)
            elif format == ReportFormat.HTML:
                content = self._render_html_report(session, tool_results, analysis)
            elif format == ReportFormat.JSON:
                content = self._render_json_report(session, tool_results, analysis)
            elif format == ReportFormat.PDF:
                content = self._render_pdf_report(session, tool_results, analysis)
            else:
                raise ValueError(f"不支持的报告格式: {format}")

            report = Report(
                session_id=session_id,
                original_question=session.original_question,
                refined_question=session.refined_question,
                generated_at=datetime.now(),
                tool_results=tool_results_dict,
                consensus_analysis=consensus_analysis,
                comprehensive_summary=analysis.comprehensive_summary,
                final_conclusion=analysis.final_conclusion,
                content=content,
            )

            self.logger.info(f"{format}格式报告生成完成，会话ID: {session_id}")

            return report
        except Exception as e:
            self.logger.error(f"生成{format}格式报告失败: {e}")
            raise

    def _render_text_report(
        self,
        session: SessionRecord,
        tool_results: List[ToolResultRecord],
        analysis: AnalysisResultRecord,
    ) -> str:
        report_parts = []

        report_parts.append("# 智能问答协调终端 - 分析报告")
        report_parts.append("")

        report_parts.append("## 1. 基本信息")
        report_parts.append(
            f"- 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_parts.append(f"- 会话ID: {session.id}")
        report_parts.append("")

        report_parts.append("## 2. 问题描述")
        report_parts.append(f"- 原始问题: {session.original_question}")
        if session.refined_question:
            report_parts.append(f"- 重构问题: {session.refined_question}")
        report_parts.append("")

        report_parts.append("## 3. 工具结果")
        for result in tool_results:
            report_parts.append(f"### 工具: {result.tool_name}")
            report_parts.append(f"- 执行状态: {'成功' if result.success else '失败'}")
            report_parts.append(f"- 执行时间: {result.execution_time:.2f}秒")
            if result.success:
                report_parts.append("- 回答:")
                report_parts.append(f'  "{result.answer}"')
            else:
                report_parts.append(f"- 错误信息: {result.error_message}")
            report_parts.append("")

        report_parts.append("## 4. 共识分析")

        report_parts.append("### 相似度矩阵")
        matrix_str = "  ".join(
            [result.tool_name[:4] for result in tool_results if result.success]
        )
        report_parts.append(f"      {matrix_str}")

        successful_results = [result for result in tool_results if result.success]
        for i, (row, result) in enumerate(
            zip(analysis.similarity_matrix, successful_results)
        ):
            row_str = "  ".join([f"{score:.2f}" for score in row])
            report_parts.append(f"{result.tool_name[:4]}:  {row_str}")
        report_parts.append("")

        report_parts.append("### 共识度评分")
        for tool, score in analysis.consensus_scores.items():
            report_parts.append(f"- {tool}: {score}分")
        report_parts.append("")

        report_parts.append("### 核心观点")
        for i, point in enumerate(analysis.key_points, 1):
            sources = ", ".join(point["sources"])
            report_parts.append(f"{i}. {point['content']} (来源: {sources})")
        report_parts.append("")

        report_parts.append("### 分歧点")
        if analysis.differences:
            for i, diff in enumerate(analysis.differences, 1):
                sources = ", ".join(diff["sources"])
                report_parts.append(f"{i}. {diff['content']} (来源: {sources})")
        else:
            report_parts.append("- 无明显分歧")
        report_parts.append("")

        report_parts.append("## 5. 综合总结")
        report_parts.append(analysis.comprehensive_summary)
        report_parts.append("")

        report_parts.append("## 6. 最终结论")
        report_parts.append(analysis.final_conclusion)
        report_parts.append("")

        report_parts.append("---")
        report_parts.append("此报告由智能问答协调终端自动生成")

        return "\n".join(report_parts)

    def _render_markdown_report(
        self,
        session: SessionRecord,
        tool_results: List[ToolResultRecord],
        analysis: AnalysisResultRecord,
    ) -> str:
        report_parts = []

        report_parts.append("# 智能问答协调终端 - 分析报告\n")

        report_parts.append("## 1. 基本信息\n")
        report_parts.append(
            f"- **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        report_parts.append(f"- **会话ID**: {session.id}\n")

        report_parts.append("## 2. 问题描述\n")
        report_parts.append(f"- **原始问题**: {session.original_question}\n")
        if session.refined_question:
            report_parts.append(f"- **重构问题**: {session.refined_question}\n")

        report_parts.append("## 3. 工具结果\n")
        for result in tool_results:
            report_parts.append(f"### {result.tool_name}\n")
            report_parts.append(
                f"- **执行状态**: {'✅ 成功' if result.success else '❌ 失败'}\n"
            )
            report_parts.append(f"- **执行时间**: {result.execution_time:.2f}秒\n")
            if result.success:
                report_parts.append(f"**回答**:\n```\n{result.answer}\n```\n")
            else:
                report_parts.append(f"- **错误信息**: {result.error_message}\n")

        report_parts.append("## 4. 共识分析\n")

        report_parts.append("### 相似度矩阵\n")
        matrix_str = " | ".join(
            [result.tool_name[:4] for result in tool_results if result.success]
        )
        report_parts.append(f"| | {matrix_str} |\n")
        report_parts.append(
            "|"
            + "---|" * (len([result for result in tool_results if result.success]) + 1)
            + "\n"
        )

        successful_results = [result for result in tool_results if result.success]
        for i, (row, result) in enumerate(
            zip(analysis.similarity_matrix, successful_results)
        ):
            row_str = " | ".join([f"{score:.2f}" for score in row])
            report_parts.append(f"| {result.tool_name[:4]} | {row_str} |\n")

        report_parts.append("### 共识度评分\n")
        for tool, score in analysis.consensus_scores.items():
            report_parts.append(f"- **{tool}**: {score}分\n")

        report_parts.append("### 核心观点\n")
        for i, point in enumerate(analysis.key_points, 1):
            sources = ", ".join(point["sources"])
            report_parts.append(f"{i}. {point['content']} *(来源: {sources})*\n")

        report_parts.append("### 分歧点\n")
        if analysis.differences:
            for i, diff in enumerate(analysis.differences, 1):
                sources = ", ".join(diff["sources"])
                report_parts.append(f"{i}. {diff['content']} *(来源: {sources})*\n")
        else:
            report_parts.append("- 无明显分歧\n")

        report_parts.append("## 5. 综合总结\n")
        report_parts.append(f"{analysis.comprehensive_summary}\n")

        report_parts.append("## 6. 最终结论\n")
        report_parts.append(f"{analysis.final_conclusion}\n")

        report_parts.append("---\n")
        report_parts.append("*此报告由智能问答协调终端自动生成*\n")

        return "".join(report_parts)

    def _render_html_report(
        self,
        session: SessionRecord,
        tool_results: List[ToolResultRecord],
        analysis: AnalysisResultRecord,
    ) -> str:
        html_parts = []

        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html lang='zh-CN'>")
        html_parts.append("<head>")
        html_parts.append("    <meta charset='UTF-8'>")
        html_parts.append(
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        )
        html_parts.append("    <title>智能问答协调终端 - 分析报告</title>")
        html_parts.append("    <style>")
        html_parts.append(
            "        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }"
        )
        html_parts.append(
            "        h1 { color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }"
        )
        html_parts.append("        h2 { color: #555; margin-top: 30px; }")
        html_parts.append("        h3 { color: #666; margin-top: 20px; }")
        html_parts.append(
            "        table { border-collapse: collapse; width: 100%; margin: 10px 0; }"
        )
        html_parts.append(
            "        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }"
        )
        html_parts.append("        th { background-color: #f2f2f2; }")
        html_parts.append("        .success { color: green; }")
        html_parts.append("        .failure { color: red; }")
        html_parts.append(
            "        .code-block { background-color: #f5f5f5; padding: 10px; border-radius: 5px; }"
        )
        html_parts.append(
            "        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; color: #666; }"
        )
        html_parts.append("    </style>")
        html_parts.append("</head>")
        html_parts.append("<body>")
        html_parts.append("    <h1>智能问答协调终端 - 分析报告</h1>")

        html_parts.append("    <h2>1. 基本信息</h2>")
        html_parts.append("    <ul>")
        html_parts.append(
            f"        <li><strong>报告生成时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>"
        )
        html_parts.append(f"        <li><strong>会话ID</strong>: {session.id}</li>")
        html_parts.append("    </ul>")

        html_parts.append("    <h2>2. 问题描述</h2>")
        html_parts.append("    <ul>")
        html_parts.append(
            f"        <li><strong>原始问题</strong>: {session.original_question}</li>"
        )
        if session.refined_question:
            html_parts.append(
                f"        <li><strong>重构问题</strong>: {session.refined_question}</li>"
            )
        html_parts.append("    </ul>")

        html_parts.append("    <h2>3. 工具结果</h2>")
        for result in tool_results:
            html_parts.append(f"    <h3>{result.tool_name}</h3>")
            html_parts.append("    <ul>")
            status_class = "success" if result.success else "failure"
            status_text = "成功" if result.success else "失败"
            html_parts.append(
                f"        <li><strong>执行状态</strong>: <span class='{status_class}'>{status_text}</span></li>"
            )
            html_parts.append(
                f"        <li><strong>执行时间</strong>: {result.execution_time:.2f}秒</li>"
            )
            if result.success:
                html_parts.append("        <li><strong>回答</strong>:</li>")
                html_parts.append(
                    f"        <div class='code-block'>{result.answer}</div>"
                )
            else:
                html_parts.append(
                    f"        <li><strong>错误信息</strong>: {result.error_message}</li>"
                )
            html_parts.append("    </ul>")

        html_parts.append("    <h2>4. 共识分析</h2>")

        html_parts.append("    <h3>相似度矩阵</h3>")
        html_parts.append("    <table>")
        html_parts.append("        <tr>")
        html_parts.append("            <th></th>")
        for result in tool_results:
            if result.success:
                html_parts.append(f"            <th>{result.tool_name[:4]}</th>")
        html_parts.append("        </tr>")

        successful_results = [result for result in tool_results if result.success]
        for i, (row, result) in enumerate(
            zip(analysis.similarity_matrix, successful_results)
        ):
            html_parts.append("        <tr>")
            html_parts.append(f"            <td>{result.tool_name[:4]}</td>")
            for score in row:
                html_parts.append(f"            <td>{score:.2f}</td>")
            html_parts.append("        </tr>")
        html_parts.append("    </table>")

        html_parts.append("    <h3>共识度评分</h3>")
        html_parts.append("    <ul>")
        for tool, score in analysis.consensus_scores.items():
            html_parts.append(f"        <li><strong>{tool}</strong>: {score}分</li>")
        html_parts.append("    </ul>")

        html_parts.append("    <h3>核心观点</h3>")
        html_parts.append("    <ol>")
        for point in analysis.key_points:
            sources = ", ".join(point["sources"])
            html_parts.append(
                f"        <li>{point['content']} <em>(来源: {sources})</em></li>"
            )
        html_parts.append("    </ol>")

        html_parts.append("    <h3>分歧点</h3>")
        if analysis.differences:
            html_parts.append("    <ul>")
            for diff in analysis.differences:
                sources = ", ".join(diff["sources"])
                html_parts.append(
                    f"        <li>{diff['content']} <em>(来源: {sources})</em></li>"
                )
            html_parts.append("    </ul>")
        else:
            html_parts.append("    <p>无明显分歧</p>")

        html_parts.append("    <h2>5. 综合总结</h2>")
        html_parts.append(f"    <p>{analysis.comprehensive_summary}</p>")

        html_parts.append("    <h2>6. 最终结论</h2>")
        html_parts.append(f"    <p>{analysis.final_conclusion}</p>")

        html_parts.append("    <div class='footer'>")
        html_parts.append("        <p>此报告由智能问答协调终端自动生成</p>")
        html_parts.append("    </div>")

        html_parts.append("</body>")
        html_parts.append("</html>")

        return "\n".join(html_parts)

    def _render_json_report(
        self,
        session: SessionRecord,
        tool_results: List[ToolResultRecord],
        analysis: AnalysisResultRecord,
    ) -> str:
        report_data = {
            "session_id": session.id,
            "original_question": session.original_question,
            "refined_question": session.refined_question,
            "generated_at": datetime.now().isoformat(),
            "tool_results": [
                {
                    "tool_name": result.tool_name,
                    "success": result.success,
                    "answer": result.answer,
                    "error_message": result.error_message,
                    "execution_time": result.execution_time,
                    "timestamp": result.timestamp.isoformat(),
                }
                for result in tool_results
            ],
            "consensus_analysis": {
                "similarity_matrix": analysis.similarity_matrix,
                "consensus_scores": analysis.consensus_scores,
                "key_points": analysis.key_points,
                "differences": analysis.differences,
            },
            "comprehensive_summary": analysis.comprehensive_summary,
            "final_conclusion": analysis.final_conclusion,
        }

        return json.dumps(report_data, ensure_ascii=False, indent=2)

    def _render_pdf_report(
        self,
        session: SessionRecord,
        tool_results: List[ToolResultRecord],
        analysis: AnalysisResultRecord,
    ) -> str:
        html_content = self._render_html_report(session, tool_results, analysis)

        try:
            import tempfile

            from weasyprint import HTML

            with tempfile.NamedTemporaryFile(
                suffix=".html", delete=False, mode="w", encoding="utf-8"
            ) as f:
                f.write(html_content)
                html_file = f.name

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                pdf_file = f.name

            HTML(html_file).write_pdf(pdf_file)

            with open(pdf_file, "rb") as f:
                pdf_content = f.read()

            os.unlink(html_file)
            os.unlink(pdf_file)

            return pdf_content
        except ImportError:
            self.logger.warning("weasyprint未安装，返回HTML格式作为PDF替代")
            return html_content
        except Exception as e:
            self.logger.error(f"生成PDF失败: {e}")
            return html_content

    def save_report(
        self,
        report: Report,
        file_path: Optional[str] = None,
        format: str = ReportFormat.TEXT,
    ) -> str:
        try:
            if not file_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs("reports", exist_ok=True)

                extension = {
                    ReportFormat.TEXT: ".txt",
                    ReportFormat.MARKDOWN: ".md",
                    ReportFormat.HTML: ".html",
                    ReportFormat.JSON: ".json",
                    ReportFormat.PDF: ".pdf",
                }.get(format, ".txt")

                file_path = f"reports/report_{report.session_id}_{timestamp}{extension}"

            if format == ReportFormat.PDF and isinstance(report.content, bytes):
                with open(file_path, "wb") as f:
                    f.write(report.content)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(report.content)

            self.logger.info(f"报告已保存到: {file_path}")

            return file_path
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
            raise

    def export_report(
        self,
        session: int,
        format: str = ReportFormat.TEXT,
        file_path: Optional[str] = None,
    ) -> str:
        try:
            report = self.generate_report(session, format)
            return self.save_report(report, file_path, format)
        except Exception as e:
            self.logger.error(f"导出报告失败: {e}")
            raise

    def get_supported_formats(self) -> List[str]:
        return [
            ReportFormat.TEXT,
            ReportFormat.MARKDOWN,
            ReportFormat.HTML,
            ReportFormat.JSON,
            ReportFormat.PDF,
        ]

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.infrastructure.data.data_manager import (
    AnalysisResultRecord,
    DataManager,
    SessionRecord,
    ToolResultRecord,
)
from src.infrastructure.logging.logger import get_logger


@dataclass
class Report:
    session_id: int
    original_question: str
    refined_question: Optional[str]
    generated_at: datetime
    tool_results: List[Dict[str, Any]]
    consensus_analysis: Dict[str, Any]
    comprehensive_summary: str
    final_conclusion: str
    content: str


class ReportGenerator:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.logger = get_logger()

    def generate_report(self, session_id: int) -> Report:
        """生成最终报告"""
        self.logger.info(f"开始生成报告，会话ID: {session_id}")

        try:
            # 获取会话信息
            session = self.data_manager.get_session(session_id)
            if not session:
                self.logger.error(f"会话 {session_id} 不存在")
                raise ValueError(f"会话 {session_id} 不存在")

            # 获取工具结果
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

            # 获取分析结果
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

            # 生成报告内容
            content = self._render_text_report(session, tool_results, analysis)

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

            self.logger.info(f"报告生成完成，会话ID: {session_id}")

            return report
        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")
            raise

    def _render_text_report(
        self,
        session: SessionRecord,
        tool_results: List[ToolResultRecord],
        analysis: AnalysisResultRecord,
    ) -> str:
        """渲染纯文本格式报告"""
        report_parts = []

        # 报告标题
        report_parts.append("# 智能问答协调终端 - 分析报告")
        report_parts.append("")

        # 基本信息
        report_parts.append("## 1. 基本信息")
        report_parts.append(
            f"- 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_parts.append(f"- 会话ID: {session.id}")
        report_parts.append("")

        # 问题描述
        report_parts.append("## 2. 问题描述")
        report_parts.append(f"- 原始问题: {session.original_question}")
        if session.refined_question:
            report_parts.append(f"- 重构问题: {session.refined_question}")
        report_parts.append("")

        # 工具结果
        report_parts.append("## 3. 工具结果")
        for result in tool_results:
            report_parts.append(f"### 工具: {result.tool_name}")
            report_parts.append(f"- 执行状态: {'成功' if result.success else '失败'}")
            report_parts.append(f"- 执行时间: {result.execution_time:.2f}秒")
            if result.success:
                report_parts.append("- 回答:")
                report_parts.append(f'  "\{result.answer}"')
            else:
                report_parts.append(f"- 错误信息: {result.error_message}")
            report_parts.append("")

        # 共识分析
        report_parts.append("## 4. 共识分析")

        # 相似度矩阵
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

        # 共识度评分
        report_parts.append("### 共识度评分")
        for tool, score in analysis.consensus_scores.items():
            report_parts.append(f"- {tool}: {score}分")
        report_parts.append("")

        # 核心观点
        report_parts.append("### 核心观点")
        for i, point in enumerate(analysis.key_points, 1):
            sources = ", ".join(point["sources"])
            report_parts.append(f"{i}. {point['content']} (来源: {sources})")
        report_parts.append("")

        # 分歧点
        report_parts.append("### 分歧点")
        if analysis.differences:
            for i, diff in enumerate(analysis.differences, 1):
                sources = ", ".join(diff["sources"])
                report_parts.append(f"{i}. {diff['content']} (来源: {sources})")
        else:
            report_parts.append("- 无明显分歧")
        report_parts.append("")

        # 综合总结
        report_parts.append("## 5. 综合总结")
        report_parts.append(analysis.comprehensive_summary)
        report_parts.append("")

        # 最终结论
        report_parts.append("## 6. 最终结论")
        report_parts.append(analysis.final_conclusion)
        report_parts.append("")

        # 报告结束
        report_parts.append("---")
        report_parts.append("此报告由智能问答协调终端自动生成")

        return "\n".join(report_parts)

    def save_report(self, report: Report, file_path: Optional[str] = None) -> str:
        """保存报告到文件"""
        try:
            if not file_path:
                file_path = f"report_{report.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report.content)

            self.logger.info(f"报告已保存到: {file_path}")

            return file_path
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
            raise

    def get_report_content(self, session_id: int) -> Optional[str]:
        """获取报告内容"""
        try:
            report = self.generate_report(session_id)
            return report.content
        except Exception as e:
            self.logger.error(f"获取报告内容失败: {e}")
            return None

    def export_report(
        self, session_id: int, format: str = "text", file_path: Optional[str] = None
    ) -> str:
        """导出报告为指定格式"""
        try:
            if format != "text":
                raise ValueError(f"不支持的报告格式: {format}")

            report = self.generate_report(session_id)
            return self.save_report(report, file_path)
        except Exception as e:
            self.logger.error(f"导出报告失败: {e}")
            raise

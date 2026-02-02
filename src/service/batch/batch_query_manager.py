import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.executor.query_executor import QueryExecutor
from src.core.reporter.multi_format_reporter import MultiFormatReporter
from src.infrastructure.data.data_manager import DataManager
from src.infrastructure.logging.logger import get_logger


@dataclass
class BatchQuestion:
    """批量查询问题"""

    question: str
    priority: str = "medium"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BatchQueryResult:
    """批量查询结果"""

    question: str
    priority: str
    session_id: Optional[int]
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    tool_results: Optional[List[Dict[str, Any]]] = None


@dataclass
class BatchReport:
    """批量查询报告"""

    total_questions: int
    success_count: int
    failure_count: int
    total_execution_time: float
    results: List[BatchQueryResult]
    generated_at: datetime
    content: str


class BatchQueryManager:
    """批量查询管理器"""

    def __init__(
        self,
        query_executor: QueryExecutor,
        data_manager: DataManager,
        multi_format_reporter: MultiFormatReporter,
    ):
        self.query_executor = query_executor
        self.data_manager = data_manager
        self.multi_format_reporter = multi_format_reporter
        self.logger = get_logger()

    def load_questions_from_file(self, file_path: str) -> List[BatchQuestion]:
        """从JSON文件加载问题列表"""
        self.logger.info(f"从文件加载问题: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("JSON文件必须包含问题列表")

            questions = []
            for idx, item in enumerate(data):
                if isinstance(item, str):
                    questions.append(BatchQuestion(question=item))
                elif isinstance(item, dict):
                    question = item.get("question")
                    if not question:
                        self.logger.warning(f"第{idx + 1}项缺少question字段，跳过")
                        continue

                    priority = item.get("priority", "medium")
                    metadata = {
                        k: v
                        for k, v in item.items()
                        if k not in ["question", "priority"]
                    }

                    questions.append(
                        BatchQuestion(
                            question=question,
                            priority=priority,
                            metadata=metadata,
                        )
                    )
                else:
                    self.logger.warning(f"第{idx + 1}项格式类型不支持，跳过")

            self.logger.info(f"成功加载 {len(questions)} 个问题")

            return questions

        except FileNotFoundError:
            self.logger.error(f"文件不存在: {file_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"加载问题文件失败: {e}")
            raise

    async def execute_batch_queries(
        self,
        questions: List[BatchQuestion],
        max_concurrent: int = 3,
    ) -> List[BatchQueryResult]:
        """执行批量查询"""
        self.logger.info(
            f"开始执行批量查询，共 {len(questions)} 个问题，"
            f"最大并发数: {max_concurrent}"
        )

        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single_question(
            question: BatchQuestion,
        ) -> BatchQueryResult:
            """执行单个问题"""
            async with semaphore:
                import time

                start_time = time.time()
                session_id = None
                success = False
                error_message = None
                tool_results = None

                try:
                    self.logger.info(f"执行问题: {question.question[:50]}...")

                    session_id = self.data_manager.save_session(
                        original_question=question.question,
                        refined_question=question.question,
                    )

                    tool_names = [
                        tool["name"]
                        for tool in self.query_executor.tool_manager.get_enabled_tools()
                    ]

                    execution_result = await self.query_executor.execute_queries(
                        session_id=session_id,
                        question=question.question,
                        tools=tool_names,
                    )

                    success = execution_result.completed
                    tool_results = [
                        {
                            "tool_name": result.tool_name,
                            "success": result.success,
                            "answer": result.answer,
                            "error_message": result.error_message,
                            "execution_time": result.execution_time,
                        }
                        for result in execution_result.tool_results
                    ]

                    self.logger.info(
                        f"问题执行完成: {question.question[:50]}..., "
                        f"会话ID: {session_id}, 成功: {success}"
                    )

                except Exception as e:
                    error_message = str(e)
                    self.logger.error(
                        f"问题执行失败: {question.question[:50]}..., "
                        f"错误: {error_message}"
                    )

                execution_time = time.time() - start_time

                return BatchQueryResult(
                    question=question.question,
                    priority=question.priority,
                    session_id=session_id,
                    success=success,
                    execution_time=execution_time,
                    error_message=error_message,
                    tool_results=tool_results,
                )

        tasks = [execute_single_question(q) for q in questions]
        results = await asyncio.gather(*tasks)

        self.logger.info(
            f"批量查询完成，成功: {sum(1 for r in results if r.success)}, "
            f"失败: {sum(1 for r in results if not r.success)}"
        )

        return results

    def generate_batch_report(
        self,
        results: List[BatchQueryResult],
        output_format: str = "markdown",
    ) -> BatchReport:
        """生成批量查询报告"""
        self.logger.info(f"开始生成批量查询报告，格式: {output_format}")

        total_questions = len(results)
        success_count = sum(1 for r in results if r.success)
        failure_count = total_questions - success_count
        total_execution_time = sum(r.execution_time for r in results)

        if output_format.lower() == "markdown":
            content = self._render_markdown_report(
                results, success_count, failure_count, total_execution_time
            )
        elif output_format.lower() == "json":
            content = self._render_json_report(
                results, success_count, failure_count, total_execution_time
            )
        elif output_format.lower() == "text":
            content = self._render_text_report(
                results, success_count, failure_count, total_execution_time
            )
        else:
            raise ValueError(f"不支持的报告格式: {output_format}")

        report = BatchReport(
            total_questions=total_questions,
            success_count=success_count,
            failure_count=failure_count,
            total_execution_time=total_execution_time,
            results=results,
            generated_at=datetime.now(),
            content=content,
        )

        self.logger.info("批量查询报告生成完成")

        return report

    def _render_markdown_report(
        self,
        results: List[BatchQueryResult],
        success_count: int,
        failure_count: int,
        total_execution_time: float,
    ) -> str:
        """渲染Markdown格式报告"""
        lines = [
            "# 批量查询报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**总问题数**: {len(results)}",
            f"**成功**: {success_count}",
            f"**失败**: {failure_count}",
            f"**总执行时间**: {total_execution_time:.2f} 秒",
            f"**平均执行时间**: {total_execution_time / len(results):.2f} 秒",
            "",
            "---",
            "",
            "## 查询详情",
            "",
        ]

        for idx, result in enumerate(results, 1):
            status_icon = "✅" if result.success else "❌"
            lines.append(f"### {idx}. {result.question[:100]}")
            status_text = "成功" if result.success else "失败"
            lines.append(f"**状态**: {status_icon} {status_text}")
            lines.append(f"**优先级**: {result.priority}")
            lines.append(f"**执行时间**: {result.execution_time:.2f} 秒")

            if result.session_id:
                lines.append(f"**会话ID**: {result.session_id}")

            if result.error_message:
                lines.append(f"**错误信息**: {result.error_message}")

            if result.tool_results:
                lines.append("")
                lines.append("**工具结果**:")
                lines.append("")
                for tool_result in result.tool_results:
                    tool_status = "✅" if tool_result["success"] else "❌"
                    answer = (
                        tool_result["answer"][:100]
                        if tool_result["success"]
                        else tool_result["error_message"]
                    )
                    lines.append(
                        f"- {tool_status} **{tool_result['tool_name']}**: {answer}"
                    )

            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _render_json_report(
        self,
        results: List[BatchQueryResult],
        success_count: int,
        failure_count: int,
        total_execution_time: float,
    ) -> str:
        """渲染JSON格式报告"""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_questions": len(results),
                "success_count": success_count,
                "failure_count": failure_count,
                "total_execution_time": total_execution_time,
                "average_execution_time": total_execution_time / len(results),
            },
            "results": [
                {
                    "question": r.question,
                    "priority": r.priority,
                    "session_id": r.session_id,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "error_message": r.error_message,
                    "tool_results": r.tool_results,
                }
                for r in results
            ],
        }

        return json.dumps(report_data, ensure_ascii=False, indent=2)

    def _render_text_report(
        self,
        results: List[BatchQueryResult],
        success_count: int,
        failure_count: int,
        total_execution_time: float,
    ) -> str:
        """渲染文本格式报告"""
        lines = [
            "=" * 80,
            "批量查询报告",
            "=" * 80,
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"总问题数: {len(results)}",
            f"成功: {success_count}",
            f"失败: {failure_count}",
            f"总执行时间: {total_execution_time:.2f} 秒",
            f"平均执行时间: {total_execution_time / len(results):.2f} 秒",
            "",
            "=" * 80,
            "",
            "查询详情",
            "=" * 80,
            "",
        ]

        for idx, result in enumerate(results, 1):
            status = "成功" if result.success else "失败"
            lines.append(f"{idx}. {result.question[:100]}")
            lines.append(f"   状态: {status}")
            lines.append(f"   优先级: {result.priority}")
            lines.append(f"   执行时间: {result.execution_time:.2f} 秒")

            if result.session_id:
                lines.append(f"   会话ID: {result.session_id}")

            if result.error_message:
                lines.append(f"   错误信息: {result.error_message}")

            if result.tool_results:
                lines.append("   工具结果:")
                for tool_result in result.tool_results:
                    tool_status = "成功" if tool_result["success"] else "失败"
                    lines.append(f"     - {tool_result['tool_name']}: {tool_status}")
                    if tool_result["success"]:
                        lines.append(f"       {tool_result['answer'][:100]}")
                    else:
                        lines.append(f"       {tool_result['error_message']}")

            lines.append("")
            lines.append("-" * 80)
            lines.append("")

        return "\n".join(lines)

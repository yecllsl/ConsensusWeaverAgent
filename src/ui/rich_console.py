import time
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.syntax import Syntax
from rich.table import Table


class RichConsole:
    """rich美化终端"""

    def __init__(self) -> None:
        self.console = Console()
        self.live: Optional[Live] = None

    def print_welcome(self) -> None:
        """打印欢迎信息"""
        welcome_text = """
        ╔════════════════════════════════════════════════════════════╗
        ║                                                              ║
        ║          智能问答协调终端 (ConsensusWeaverAgent)              ║
        ║                                                              ║
        ║          版本: 0.4.0.dev0                                    ║
        ║          一个能够协调多个AI工具并生成综合报告的智能系统        ║
        ║                                                              ║
        ╚════════════════════════════════════════════════════════════╝
        """
        self.console.print(Panel(welcome_text, style="bold blue"))

    def print_question(self, question: str) -> None:
        """打印问题"""
        self.console.print(
            Panel(f"📝 问题: {question}", title="用户输入", style="green")
        )

    def print_progress(self, task_id: str, description: str, total: int) -> None:
        """打印进度条"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(description, total=total)
            for i in range(total):
                progress.update(task, advance=1)
                time.sleep(0.1)

    def print_tool_result(self, tool_name: str, result: str, success: bool) -> None:
        """打印工具结果"""
        style = "green" if success else "red"
        icon = "✅" if success else "❌"
        self.console.print(Panel(result, title=f"{icon} {tool_name}", style=style))

    def print_consensus_analysis(self, analysis: Dict[str, Any]) -> None:
        """打印共识分析"""
        table = Table(title="共识度分析")
        table.add_column("工具", style="cyan")
        table.add_column("共识度", style="magenta")
        table.add_column("状态", style="green")

        for tool, score in analysis.get("consensus_scores", {}).items():
            table.add_row(tool, f"{score:.2f}", "✓")

        self.console.print(table)

    def print_report(self, report: str) -> None:
        """打印报告"""
        self.console.print(Panel(report, title="分析报告", style="yellow"))

    def print_error(self, error: str) -> None:
        """打印错误"""
        self.console.print(Panel(error, title="错误", style="bold red"))

    def print_warning(self, warning: str) -> None:
        """打印警告"""
        self.console.print(Panel(warning, title="警告", style="bold yellow"))

    def print_info(self, info: str) -> None:
        """打印信息"""
        self.console.print(Panel(info, title="信息", style="bold blue"))

    def print_table(self, data: List[Dict[str, Any]], title: str) -> None:
        """打印表格"""
        if not data:
            return

        table = Table(title=title)
        for key in data[0].keys():
            table.add_column(key)

        for row in data:
            table.add_row(*[str(v) for v in row.values()])

        self.console.print(table)

    def print_syntax(self, code: str, language: str = "python") -> None:
        """打印语法高亮代码"""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)

    def clear_screen(self) -> None:
        """清屏"""
        self.console.clear()

    def input(self, prompt: str = "") -> str:
        """输入"""
        result = self.console.input(prompt)
        return str(result) if result is not None else ""

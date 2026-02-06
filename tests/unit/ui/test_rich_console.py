from unittest.mock import patch

from src.ui.rich_console import RichConsole


class TestRichConsole:
    """测试RichConsole类"""

    def test_init(self) -> None:
        """测试初始化"""
        console = RichConsole()
        assert console.console is not None
        assert console.live is None

    def test_print_welcome(self) -> None:
        """测试打印欢迎信息"""
        console = RichConsole()
        with patch.object(console.console, "print") as mock_print:
            console.print_welcome()
            mock_print.assert_called_once()

    def test_print_question(self) -> None:
        """测试打印问题"""
        console = RichConsole()
        with patch.object(console.console, "print") as mock_print:
            console.print_question("测试问题")
            mock_print.assert_called_once()

    def test_print_tool_result_success(self) -> None:
        """测试打印工具结果（成功）"""
        console = RichConsole()
        with patch.object(console.console, "print") as mock_print:
            console.print_tool_result("test_tool", "测试结果", True)
            mock_print.assert_called_once()

    def test_print_tool_result_failure(self) -> None:
        """测试打印工具结果（失败）"""
        console = RichConsole()
        with patch.object(console.console, "print") as mock_print:
            console.print_tool_result("test_tool", "错误信息", False)
            mock_print.assert_called_once()

    def test_print_consensus_analysis(self) -> None:
        """测试打印共识分析"""
        console = RichConsole()
        analysis = {
            "consensus_scores": {
                "tool1": 0.85,
                "tool2": 0.75,
            }
        }
        with patch.object(console.console, "print") as mock_print:
            console.print_consensus_analysis(analysis)
            mock_print.assert_called_once()

    def test_print_report(self) -> None:
        """测试打印报告"""
        console = RichConsole()
        with patch.object(console.console, "print") as mock_print:
            console.print_report("测试报告")
            mock_print.assert_called_once()

    def test_print_error(self) -> None:
        """测试打印错误"""
        console = RichConsole()
        with patch.object(console.console, "print") as mock_print:
            console.print_error("测试错误")
            mock_print.assert_called_once()

    def test_print_warning(self) -> None:
        """测试打印警告"""
        console = RichConsole()
        with patch.object(console.console, "print") as mock_print:
            console.print_warning("测试警告")
            mock_print.assert_called_once()

    def test_print_info(self) -> None:
        """测试打印信息"""
        console = RichConsole()
        with patch.object(console.console, "print") as mock_print:
            console.print_info("测试信息")
            mock_print.assert_called_once()

    def test_print_table(self) -> None:
        """测试打印表格"""
        console = RichConsole()
        data = [
            {"name": "tool1", "score": 0.85},
            {"name": "tool2", "score": 0.75},
        ]
        with patch.object(console.console, "print") as mock_print:
            console.print_table(data, "测试表格")
            mock_print.assert_called_once()

    def test_print_table_empty(self) -> None:
        """测试打印空表格"""
        console = RichConsole()
        data = []
        with patch.object(console.console, "print") as mock_print:
            console.print_table(data, "测试表格")
            mock_print.assert_not_called()

    def test_print_syntax(self) -> None:
        """测试打印语法高亮代码"""
        console = RichConsole()
        with patch.object(console.console, "print") as mock_print:
            console.print_syntax("print('hello')", "python")
            mock_print.assert_called_once()

    def test_clear_screen(self) -> None:
        """测试清屏"""
        console = RichConsole()
        with patch.object(console.console, "clear") as mock_clear:
            console.clear_screen()
            mock_clear.assert_called_once()

    def test_input(self) -> None:
        """测试输入"""
        console = RichConsole()
        with patch.object(
            console.console, "input", return_value="test_input"
        ) as mock_input:
            result = console.input("请输入: ")
            assert result == "test_input"
            mock_input.assert_called_once_with("请输入: ")

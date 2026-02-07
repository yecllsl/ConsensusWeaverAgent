"""测试主模块"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.ui.tui_manager import get_tui_manager


class TestCLICommands:
    """测试CLI命令"""

    def test_cli_help(self):
        """测试CLI帮助"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "智能问答协调终端应用" in result.output

    def test_run_command_help(self):
        """测试run命令帮助"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])

        assert result.exit_code == 0
        assert "运行交互式问答会话" in result.output

    def test_ask_command_help(self):
        """测试ask命令帮助"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["ask", "--help"])

        assert result.exit_code == 0
        assert "直接询问单个问题" in result.output

    def test_check_command_help(self):
        """测试check命令帮助"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["check", "--help"])

        assert result.exit_code == 0
        assert "检查系统环境和依赖" in result.output

    def test_version_command_help(self):
        """测试version命令帮助"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["version", "--help"])

        assert result.exit_code == 0
        assert "显示版本信息" in result.output

    def test_version_command(self):
        """测试version命令"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "0.4.0.dev0" in result.output


class TestAgentSelection:
    """测试Agent选择"""

    @patch("src.main.run_interactive_session")
    def test_run_command_with_iflow_agent(self, mock_run_session):
        """测试使用iflow agent"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--iflow"])

        assert result.exit_code == 0

    @patch("src.main.run_interactive_session")
    def test_run_command_with_qwen_agent(self, mock_run_session):
        """测试使用qwen agent"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--qwen"])

        assert result.exit_code == 0

    @patch("src.main.run_interactive_session")
    def test_run_command_with_codebuddy_agent(self, mock_run_session):
        """测试使用codebuddy agent"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--codebuddy"])

        assert result.exit_code == 0


class TestAskCommand:
    """测试ask命令"""

    @patch("src.main.run_single_question")
    def test_ask_command_with_question(self, mock_run_single):
        """测试ask命令带问题"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["ask", "什么是Python？"])

        assert result.exit_code == 0

    @patch("src.main.run_single_question")
    def test_ask_command_with_output(self, mock_run_single):
        """测试ask命令带输出文件"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["ask", "什么是Python？", "--output", "output.txt"])

        assert result.exit_code == 0


class TestCheckCommand:
    """测试check命令"""

    @patch("src.main.ConfigManager")
    @patch("src.main.LLMService")
    @patch("src.main.ToolManager")
    @patch("src.main.DataManager")
    def test_check_command_success(
        self,
        mock_data_manager,
        mock_tool_manager,
        mock_llm_service,
        mock_config_manager,
    ):
        """测试check命令成功"""
        from src.main import cli

        mock_config = MagicMock()
        mock_config_manager.return_value.get_config.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(cli, ["check"])

        assert result.exit_code == 0


class TestConfigOptions:
    """测试配置选项"""

    @patch("src.main.run_interactive_session")
    def test_config_option(self, mock_run_session):
        """测试配置选项"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--config", "test.yaml", "run"])

        assert result.exit_code == 0

    @patch("src.main.run_interactive_session")
    def test_verbose_option(self, mock_run_session):
        """测试详细日志选项"""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "run"])

        assert result.exit_code == 0


class TestTUICommand:
    """测试TUI命令"""

    def test_tui_command_exists(self):
        """测试TUI命令存在"""
        from src.main import cli
        from src.ui.tui_manager import get_tui_manager

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0

        if (
            get_tui_manager().is_trogon_available()
            and get_tui_manager().is_tui_enabled()
        ):
            assert "tui" in result.output
        else:
            assert "tui" not in result.output

    @pytest.mark.skipif(
        not get_tui_manager()._trogon_available,
        reason="Trogon不可用",
    )
    def test_tui_command_help(self):
        """测试TUI命令帮助"""
        from src.main import cli
        from src.ui.tui_manager import get_tui_manager

        tui_manager = get_tui_manager()
        tui_manager.enable_tui(cli)
        tui_manager.add_tui_command_to_group(cli)

        runner = CliRunner()
        result = runner.invoke(cli, ["tui", "--help"])

        assert result.exit_code == 0
        assert "启动TUI界面" in result.output

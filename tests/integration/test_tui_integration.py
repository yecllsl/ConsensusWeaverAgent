import pytest
from click.testing import CliRunner

from src.main import cli
from src.ui.tui_manager import get_tui_manager


class TestCLIIntegration:
    """测试CLI集成"""

    def test_cli_help(self) -> None:
        """测试CLI命令帮助"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "智能问答协调终端应用" in result.output
        assert "Commands:" in result.output

    def test_cli_commands_list(self) -> None:
        """测试CLI命令列表"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "run" in result.output
        assert "ask" in result.output
        assert "check" in result.output
        assert "version" in result.output

    def test_tui_command_exists(self) -> None:
        """测试TUI命令是否存在"""
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

    def test_run_command_help(self) -> None:
        """测试run命令帮助"""
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])

        assert result.exit_code == 0
        assert "运行交互式问答会话" in result.output

    def test_ask_command_help(self) -> None:
        """测试ask命令帮助"""
        runner = CliRunner()
        result = runner.invoke(cli, ["ask", "--help"])

        assert result.exit_code == 0
        assert "直接询问单个问题" in result.output
        assert "QUESTION" in result.output

    def test_check_command_help(self) -> None:
        """测试check命令帮助"""
        runner = CliRunner()
        result = runner.invoke(cli, ["check", "--help"])

        assert result.exit_code == 0
        assert "检查系统环境和依赖" in result.output

    def test_version_command_help(self) -> None:
        """测试version命令帮助"""
        runner = CliRunner()
        result = runner.invoke(cli, ["version", "--help"])

        assert result.exit_code == 0
        assert "显示版本信息" in result.output

    def test_config_option(self) -> None:
        """测试配置选项"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--config", "test.yaml", "--help"])

        assert result.exit_code == 0

    def test_verbose_option(self) -> None:
        """测试详细日志选项"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "--help"])

        assert result.exit_code == 0

    def test_version_command(self) -> None:
        """测试version命令"""
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "0.4.0.dev0" in result.output

    def test_check_command(self) -> None:
        """测试check命令"""
        runner = CliRunner()
        result = runner.invoke(cli, ["check"])

        assert result.exit_code == 0


class TestTUIIntegration:
    """测试TUI集成"""

    @pytest.mark.skipif(
        not get_tui_manager()._trogon_available,
        reason="Trogon不可用",
    )
    def test_tui_command_help(self) -> None:
        """测试TUI命令帮助"""
        tui_manager = get_tui_manager()
        tui_manager.enable_tui(cli)
        tui_manager.add_tui_command_to_group(cli)

        runner = CliRunner()
        result = runner.invoke(cli, ["tui", "--help"])

        assert result.exit_code == 0

    @pytest.mark.skipif(
        not get_tui_manager()._trogon_available,
        reason="Trogon不可用",
    )
    def test_tui_command_tui_help(self) -> None:
        """测试TUI命令的tui子命令帮助"""
        tui_manager = get_tui_manager()
        tui_manager.enable_tui(cli)
        tui_manager.add_tui_command_to_group(cli)

        runner = CliRunner()
        result = runner.invoke(cli, ["tui", "tui", "--help"])

        assert result.exit_code == 0
        assert "启动TUI界面" in result.output


class TestCLIAndTUICompatibility:
    """测试CLI和TUI兼容性"""

    def test_cli_works_without_tui(self) -> None:
        """测试CLI在没有TUI的情况下工作"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Commands:" in result.output

    def test_all_commands_have_help(self) -> None:
        """测试所有命令都有帮助信息"""
        runner = CliRunner()

        commands = ["run", "ask", "check", "version"]

        if get_tui_manager().is_trogon_available():
            commands.append("tui")

        for command in commands:
            result = runner.invoke(cli, [command, "--help"])
            assert result.exit_code == 0, f"命令 {command} 帮助信息不可用"

    def test_backward_compatibility(self) -> None:
        """测试向后兼容性"""
        runner = CliRunner()

        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0

        result = runner.invoke(cli, ["check"])
        assert result.exit_code == 0


class TestTerminalCompatibility:
    """测试终端兼容性"""

    def test_environment_check(self) -> None:
        """测试环境检查"""
        tui_manager = get_tui_manager()
        env_info = tui_manager.check_environment()

        assert isinstance(env_info, dict)
        assert "platform" in env_info
        assert "terminal" in env_info
        assert "terminal_width" in env_info
        assert "terminal_height" in env_info

    def test_color_support(self) -> None:
        """测试颜色支持"""
        tui_manager = get_tui_manager()
        env_info = tui_manager.check_environment()

        assert isinstance(env_info["supports_color"], bool)

    def test_unicode_support(self) -> None:
        """测试Unicode支持"""
        tui_manager = get_tui_manager()
        env_info = tui_manager.check_environment()

        assert isinstance(env_info["supports_unicode"], bool)

    def test_terminal_dimensions(self) -> None:
        """测试终端尺寸"""
        tui_manager = get_tui_manager()
        env_info = tui_manager.check_environment()

        assert isinstance(env_info["terminal_width"], int)
        assert isinstance(env_info["terminal_height"], int)
        assert env_info["terminal_width"] > 0
        assert env_info["terminal_height"] > 0


class TestOutputFormatting:
    """测试输出格式化"""

    def test_help_output_formatting(self) -> None:
        """测试帮助输出格式化"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert len(result.output) > 0

    def test_version_output_formatting(self) -> None:
        """测试版本输出格式化"""
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "ConsensusWeaverAgent" in result.output
        assert "0.4.0.dev0" in result.output

    def test_error_output_formatting(self) -> None:
        """测试错误输出格式化"""
        runner = CliRunner()
        result = runner.invoke(cli, ["ask"])

        assert result.exit_code != 0
        assert len(result.output) > 0

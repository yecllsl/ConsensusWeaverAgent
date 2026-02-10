import pytest
from click.testing import CliRunner

from src.ui.tui_manager import TUIManager, get_tui_manager, setup_tui


class TestTUIManager:
    """测试TUIManager类"""

    def test_init(self) -> None:
        """测试初始化"""
        manager = TUIManager()

        assert manager is not None
        assert manager._cli_group is None
        assert manager._tui_enabled is False
        assert isinstance(manager._trogon_available, bool)

    def test_check_trogon_available(self) -> None:
        """检查Trogon可用性"""
        manager = TUIManager()

        if manager._trogon_available:
            assert manager.is_trogon_available() is True
        else:
            assert manager.is_trogon_available() is False

    def test_is_tui_enabled_initially(self) -> None:
        """测试初始TUI状态"""
        manager = TUIManager()

        assert manager.is_tui_enabled() is False

    def test_enable_tui_without_trogon(self) -> None:
        """测试在没有Trogon的情况下启用TUI"""
        manager = TUIManager()

        if manager._trogon_available:
            pytest.skip("Trogon可用，跳过此测试")

        import click

        cli_group = click.Group(name="test")
        manager.enable_tui(cli_group)

        assert manager.is_tui_enabled() is False

    def test_enable_tui_with_trogon(self) -> None:
        """测试在有Trogon的情况下启用TUI"""
        manager = TUIManager()

        if not manager._trogon_available:
            pytest.skip("Trogon不可用，跳过此测试")

        import click

        cli_group = click.Group(name="test")
        manager.enable_tui(cli_group)

        assert manager.is_tui_enabled() is True
        assert manager._cli_group is not None

    def test_disable_tui(self) -> None:
        """测试禁用TUI"""
        manager = TUIManager()

        if not manager._trogon_available:
            pytest.skip("Trogon不可用，跳过此测试")

        import click

        cli_group = click.Group(name="test")
        manager.enable_tui(cli_group)
        assert manager.is_tui_enabled() is True

        manager.disable_tui()
        assert manager.is_tui_enabled() is False

    def test_add_tui_command_to_group_without_trogon(self) -> None:
        """测试在没有Trogon的情况下添加TUI命令"""
        manager = TUIManager()

        if manager._trogon_available:
            pytest.skip("Trogon可用，跳过此测试")

        import click

        cli_group = click.Group(name="test")
        initial_commands = set(cli_group.list_commands(ctx=None))

        manager.add_tui_command_to_group(cli_group)

        final_commands = set(cli_group.list_commands(ctx=None))
        assert initial_commands == final_commands

    def test_add_tui_command_to_group_with_trogon(self) -> None:
        """测试在有Trogon的情况下添加TUI命令"""
        manager = TUIManager()

        if not manager._trogon_available:
            pytest.skip("Trogon不可用，跳过此测试")

        import click

        cli_group = click.Group(name="test")
        initial_commands = set(cli_group.list_commands(ctx=None))

        manager.enable_tui(cli_group)
        manager.add_tui_command_to_group(cli_group)

        final_commands = set(cli_group.list_commands(ctx=None))
        assert "tui" in final_commands
        assert len(final_commands) == len(initial_commands) + 1

    def test_check_environment(self) -> None:
        """测试环境检查"""
        manager = TUIManager()
        env_info = manager.check_environment()

        assert isinstance(env_info, dict)
        assert "trogon_available" in env_info
        assert "platform" in env_info
        assert "terminal" in env_info
        assert "terminal_width" in env_info
        assert "terminal_height" in env_info
        assert "supports_color" in env_info
        assert "supports_unicode" in env_info

        assert isinstance(env_info["trogon_available"], bool)
        assert isinstance(env_info["platform"], str)
        assert isinstance(env_info["terminal"], str)
        assert isinstance(env_info["terminal_width"], int)
        assert isinstance(env_info["terminal_height"], int)
        assert isinstance(env_info["supports_color"], bool)
        assert isinstance(env_info["supports_unicode"], bool)

    def test_is_compatible_with_trogon(self) -> None:
        """测试在有Trogon的情况下兼容性检查"""
        manager = TUIManager()

        if not manager._trogon_available:
            pytest.skip("Trogon不可用，跳过此测试")

        if manager.console.width < 80:
            pytest.skip("终端宽度不足，跳过此测试")

        if not manager.console.is_terminal:
            pytest.skip("非终端环境，跳过此测试")

        assert manager.is_compatible() is True

    def test_is_compatible_without_trogon(self) -> None:
        """测试在没有Trogon的情况下兼容性检查"""
        manager = TUIManager()

        if manager._trogon_available:
            pytest.skip("Trogon可用，跳过此测试")

        assert manager.is_compatible() is False


class TestGetTUIManager:
    """测试get_tui_manager函数"""

    def test_singleton(self) -> None:
        """测试单例模式"""
        manager1 = get_tui_manager()
        manager2 = get_tui_manager()

        assert manager1 is manager2


class TestSetupTUI:
    """测试setup_tui函数"""

    def test_setup_tui_enable(self) -> None:
        """测试启用TUI设置"""
        import click

        cli_group = click.Group(name="test")

        setup_tui(cli_group, enable=True)

        commands = cli_group.list_commands(ctx=None)

        if get_tui_manager()._trogon_available:
            assert "tui" in commands
        else:
            assert "tui" not in commands

    def test_setup_tui_disable(self) -> None:
        """测试禁用TUI设置"""
        import click

        cli_group = click.Group(name="test")

        setup_tui(cli_group, enable=False)

        commands = cli_group.list_commands(ctx=None)
        assert "tui" not in commands


class TestTUICommandExecution:
    """测试TUI命令执行"""

    @pytest.mark.skipif(
        not get_tui_manager()._trogon_available,
        reason="Trogon不可用",
    )
    def test_tui_command_help(self) -> None:
        """测试TUI命令帮助"""
        import click

        cli_group = click.Group(name="test")
        manager = get_tui_manager()
        manager.enable_tui(cli_group)
        manager.add_tui_command_to_group(cli_group)

        runner = CliRunner()
        result = runner.invoke(cli_group, ["tui", "--help"])

        assert result.exit_code == 0

    @pytest.mark.skipif(
        not get_tui_manager()._trogon_available,
        reason="Trogon不可用",
    )
    def test_tui_command_options(self) -> None:
        """测试TUI命令选项"""
        import click

        cli_group = click.Group(name="test")
        manager = get_tui_manager()
        manager.enable_tui(cli_group)
        manager.add_tui_command_to_group(cli_group)

        runner = CliRunner()
        result = runner.invoke(cli_group, ["tui", "tui", "--help"])

        assert result.exit_code == 0

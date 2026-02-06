import os
import sys
from typing import Any, Optional

import click
from rich.console import Console


class TUIManager:
    """TUI管理器 - 管理Trogon集成和TUI模式"""

    def __init__(self) -> None:
        self.console = Console()
        self._trogon_available = self._check_trogon_available()
        self._tui_enabled = False
        self._cli_group: Optional[click.Group] = None

    def _check_trogon_available(self) -> bool:
        """检查Trogon是否可用"""
        try:
            import importlib.util

            return importlib.util.find_spec("trogon") is not None
        except Exception:
            return False

    def is_trogon_available(self) -> bool:
        """检查Trogon是否可用"""
        return self._trogon_available

    def is_tui_enabled(self) -> bool:
        """检查TUI是否已启用"""
        return self._tui_enabled

    def enable_tui(self, cli_group: click.Group) -> None:
        """启用TUI模式"""
        if not self._trogon_available:
            self.console.print(
                "[yellow]警告: Trogon不可用，无法启用TUI模式[/yellow]"
            )
            return

        self._cli_group = cli_group
        self._tui_enabled = True

    def disable_tui(self) -> None:
        """禁用TUI模式"""
        self._tui_enabled = False

    def add_tui_command_to_group(self, cli_group: click.Group) -> None:
        """将TUI命令添加到Click组"""
        if not self._trogon_available:
            self.console.print(
                "[yellow]无法添加TUI命令: Trogon不可用[/yellow]"
            )
            return

        try:
            import trogon  # type: ignore

            @click.command()
            @click.option(
                "--theme",
                default="dark",
                type=click.Choice(["dark", "light", "monokai"]),
                help="TUI主题",
            )
            @click.option(
                "--mouse",
                is_flag=True,
                default=True,
                help="启用鼠标支持",
            )
            def tui(theme: str, mouse: bool) -> None:
                """启动TUI界面"""
                pass

            tui_command = trogon.tui(
                name="consensusweaver", command="tui", help="启动TUI界面"
            )(tui)
            cli_group.add_command(tui_command, name="tui")
            self.console.print("[green]TUI命令已添加到CLI组[/green]")

        except Exception as e:
            self.console.print(f"[red]添加TUI命令失败: {e}[/red]")

    def check_environment(self) -> dict[str, Any]:
        """检查环境兼容性"""
        env_info = {
            "trogon_available": self._trogon_available,
            "platform": sys.platform,
            "terminal": os.environ.get("TERM", "unknown"),
            "terminal_width": self.console.width,
            "terminal_height": self.console.height,
            "supports_color": self.console.is_terminal,
            "supports_unicode": True,
        }

        return env_info

    def print_environment_info(self) -> None:
        """打印环境信息"""
        env_info = self.check_environment()

        from rich.panel import Panel
        from rich.table import Table

        table = Table(title="TUI环境信息")
        table.add_column("属性", style="cyan")
        table.add_column("值", style="green")

        table.add_row("Trogon可用", "是" if env_info["trogon_available"] else "否")
        table.add_row("平台", env_info["platform"])
        table.add_row("终端", env_info["terminal"])
        table.add_row("终端宽度", str(env_info["terminal_width"]))
        table.add_row("终端高度", str(env_info["terminal_height"]))
        table.add_row("支持颜色", "是" if env_info["supports_color"] else "否")
        table.add_row("支持Unicode", "是" if env_info["supports_unicode"] else "否")

        self.console.print(Panel(table, title="环境检查", style="bold blue"))

    def is_compatible(self) -> bool:
        """检查当前环境是否兼容TUI"""
        env_info = self.check_environment()

        if not env_info["trogon_available"]:
            return False

        if not env_info["supports_color"]:
            return False

        if env_info["terminal_width"] < 80:
            return False

        return True


_tui_manager: Optional[TUIManager] = None


def get_tui_manager() -> TUIManager:
    """获取TUI管理器单例"""
    global _tui_manager
    if _tui_manager is None:
        _tui_manager = TUIManager()
    return _tui_manager


def setup_tui(cli_group: click.Group, enable: bool = True) -> None:
    """设置TUI"""
    tui_manager = get_tui_manager()

    if enable and tui_manager.is_trogon_available():
        tui_manager.enable_tui(cli_group)
        tui_manager.add_tui_command_to_group(cli_group)
    else:
        tui_manager.disable_tui()

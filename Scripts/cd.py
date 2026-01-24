#!/usr/bin/env python3
"""
ConsensusWeaverAgent CD脚本

持续部署脚本，自动化版本管理、代码检查、测试、构建和发布流程。
基于CI脚本模式实现，支持跨平台运行。
"""

import argparse
import logging
import os
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from typing import List, Optional, Tuple

# 配置默认值
DEFAULT_CONFIG = {
    "PYTHON_VERSION": "3.12",
    "UV_VERSION": "0.9.0",
    "PROJECT_DIR": os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "PYPI_INDEX_URL": "https://upload.pypi.org/legacy/",
    "TEST_PYPI_INDEX_URL": "https://test.pypi.org/legacy/",
    "BUILD_DIR": "dist",
}


# 颜色定义（使用ANSI转义序列，支持跨平台）
class Colors:
    """终端颜色定义"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    @staticmethod
    def supported() -> bool:
        """检查终端是否支持颜色"""
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def get_color(color: str) -> str:
    """获取颜色代码"""
    if not Colors.supported():
        return ""
    return getattr(Colors, color.upper(), Colors.RESET)


def print_color(message: str, color: str = "reset") -> None:
    """打印带颜色的消息"""
    print(f"{get_color(color)}{message}{get_color('reset')}")


def print_section(title: str) -> None:
    """打印节标题"""
    print_color(f"\n{'=' * 60}", "blue")
    print_color(f"{title:^60}", "blue")
    print_color(f"{'=' * 60}", "blue")


def print_subsection(title: str) -> None:
    """打印子节标题"""
    print_color(f"\n{title}", "cyan")
    print_color("-" * len(title), "cyan")


@dataclass
class CDConfig:
    """CD配置类"""

    python_version: str
    uv_version: str
    project_dir: str
    pypi_index_url: str
    test_pypi_index_url: str
    build_dir: str
    log_level: str
    config_file: Optional[str]
    skip_checks: bool
    skip_tests: bool
    skip_build: bool
    skip_publish: bool
    skip_git: bool
    use_test_pypi: bool
    dry_run: bool
    version_bump: Optional[str]
    create_git_tag: bool
    push_git_tag: bool


class CDError(Exception):
    """CD执行错误"""

    pass


class CD:
    """CD脚本主类"""

    def __init__(self, config: CDConfig):
        self.config = config
        self.logger = self._setup_logger()
        self._setup_environment()
        self.current_version = self._get_current_version()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("CD")
        logger.setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO))

        # 控制台日志
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 文件日志
        log_dir = os.path.join(self.config.project_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "cd.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        return logger

    def _setup_environment(self) -> None:
        """设置环境变量"""
        pass

    def _run_command(
        self, cmd: List[str], cwd: Optional[str] = None, quiet: bool = False
    ) -> Tuple[bool, str]:
        """运行命令并返回结果

        Args:
            cmd: 命令列表
            cwd: 工作目录
            quiet: 是否静默运行

        Returns:
            (成功标志, 输出内容)
        """
        self.logger.debug(f"执行命令: {' '.join(cmd)}")
        if not quiet:
            print_color(f"执行: {' '.join(cmd)}", "purple")

        try:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=False
            )
            output = result.stdout + result.stderr
            self.logger.debug(f"命令输出: {output}")

            if not quiet:
                if output:
                    print(output)

            return result.returncode == 0, output
        except Exception as e:
            error_msg = f"命令执行失败: {e}"
            self.logger.error(error_msg)
            if not quiet:
                print_color(error_msg, "red")
            return False, str(e)

    def _command_exists(self, command: str) -> bool:
        """检查命令是否存在"""
        return (
            subprocess.run(
                [command, "--version"] if command != "python" else [command, "-V"],
                capture_output=True,
                text=True,
            ).returncode
            == 0
        )

    def _get_current_version(self) -> str:
        """从pyproject.toml获取当前版本"""
        pyproject_path = os.path.join(self.config.project_dir, "pyproject.toml")
        if not os.path.exists(pyproject_path):
            raise CDError(f"pyproject.toml不存在: {pyproject_path}")

        with open(pyproject_path, "rb") as f:
            data: dict[str, object] = tomllib.load(f)
            project_data = data.get("project")
            if not isinstance(project_data, dict):
                raise CDError("pyproject.toml中缺少project配置")
            version = project_data.get("version")
            if not isinstance(version, str):
                raise CDError("无法从pyproject.toml获取版本号")
            return version

    def _bump_version(self, bump_type: str) -> str:
        """更新版本号

        Args:
            bump_type: 版本更新类型 (major, minor, patch)

        Returns:
            新版本号
        """
        if bump_type not in ["major", "minor", "patch"]:
            raise CDError(f"无效的版本更新类型: {bump_type}")

        # 解析当前版本
        parts = self.current_version.split(".")
        if len(parts) < 3:
            raise CDError(f"无效的版本号格式: {self.current_version}")

        # 移除.dev后缀（例如：0.2.0.dev0 -> 0.2.0）
        patch_part = parts[2]
        if ".dev" in patch_part:
            patch_part = patch_part.split(".dev")[0]

        try:
            version_parts = [int(parts[0]), int(parts[1]), int(patch_part)]
        except ValueError as e:
            raise CDError(f"无效的版本号格式: {self.current_version}, 错误: {e}")

        # 更新版本
        if bump_type == "major":
            version_parts[0] += 1
            version_parts[1] = 0
            version_parts[2] = 0
        elif bump_type == "minor":
            version_parts[1] += 1
            version_parts[2] = 0
        elif bump_type == "patch":
            version_parts[2] += 1

        new_version = f"{version_parts[0]}.{version_parts[1]}.{version_parts[2]}"

        # 更新pyproject.toml
        pyproject_path = os.path.join(self.config.project_dir, "pyproject.toml")
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 替换版本号
        import re

        content = re.sub(
            rf'version = "{self.current_version}"',
            f'version = "{new_version}"',
            content,
        )

        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.logger.info(f"版本号已更新: {self.current_version} -> {new_version}")
        print_color(
            f"✅ 版本号已更新: {self.current_version} -> {new_version}", "green"
        )

        return new_version

    def check_environment(self) -> bool:
        """检查部署环境"""
        print_section("检查部署环境")

        # 检查Python
        print_subsection("检查Python版本")
        python_cmd = None
        if self._command_exists("python"):
            python_cmd = "python"
        elif self._command_exists("python3"):
            python_cmd = "python3"
        else:
            self.logger.error("Python未安装")
            print_color("❌ Python未安装", "red")
            return False

        # 检查Python版本
        version_cmd = [python_cmd, "--version"]
        result = subprocess.run(version_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            self.logger.error("无法获取Python版本")
            print_color("❌ 无法获取Python版本", "red")
            return False

        version_output = result.stdout.strip()
        self.logger.info(f"当前Python版本: {version_output}")
        print_color(f"ℹ️ 当前Python版本: {version_output}", "blue")

        # 检查版本是否符合要求
        if self.config.python_version not in version_output:
            self.logger.error(f"需要Python {self.config.python_version}或更高版本")
            print_color(f"❌ 需要Python {self.config.python_version}或更高版本", "red")
            return False

        print_color("✅ Python版本符合要求", "green")

        # 检查uv
        print_subsection("检查uv依赖管理工具")
        if not self._command_exists("uv"):
            self.logger.error("uv未安装")
            print_color("❌ uv未安装", "red")
            return False

        # 获取uv版本
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            uv_version = result.stdout.strip()
            self.logger.info(f"uv版本: {uv_version}")
            print_color(f"✅ uv已安装: {uv_version}", "green")
        else:
            self.logger.error("无法获取uv版本")
            print_color("❌ 无法获取uv版本", "red")
            return False

        # 检查Git
        print_subsection("检查Git版本控制")
        if not self._command_exists("git"):
            self.logger.warning("Git未安装，将跳过Git相关操作")
            print_color("⚠️ Git未安装，将跳过Git相关操作", "yellow")
            self.config.skip_git = True
        else:
            # 获取Git版本
            result = subprocess.run(
                ["git", "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                git_version = result.stdout.strip()
                self.logger.info(f"Git版本: {git_version}")
                print_color(f"✅ Git已安装: {git_version}", "green")
            else:
                self.logger.warning("无法获取Git版本")
                print_color("⚠️ 无法获取Git版本", "yellow")

        print_color("✅ 环境检查完成", "green")
        return True

    def run_checks(self) -> bool:
        """运行代码检查"""
        if self.config.skip_checks:
            self.logger.info("跳过代码检查")
            return True

        print_section("运行代码检查")

        # 使用ruff检查代码格式
        print_subsection("使用ruff检查代码格式")
        cmd = ["uv", "run", "ruff", "check", "--output-format=github", "."]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("代码格式检查失败")
            print_color("❌ 代码格式检查失败", "red")
            return False

        print_color("✅ 代码格式检查通过", "green")

        # 使用mypy进行类型检查
        print_subsection("使用mypy进行类型检查")
        cmd = [
            "uv",
            "run",
            "mypy",
            "--namespace-packages",
            "--ignore-missing-imports",
            "--follow-imports=skip",
            "--strict",
            "src/",
        ]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("类型检查失败")
            print_color("❌ 类型检查失败", "red")
            return False

        print_color("✅ 类型检查通过", "green")
        print_color("✅ 所有代码检查通过", "green")
        return True

    def run_tests(self) -> bool:
        """运行测试"""
        if self.config.skip_tests:
            self.logger.info("跳过测试")
            return True

        print_section("运行测试")

        # 使用pytest运行测试
        print_subsection("使用pytest运行测试")
        cmd = ["uv", "run", "pytest", "tests/", "-v", "--tb=short", "-n", "auto"]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("测试失败")
            print_color("❌ 测试失败", "red")
            return False

        print_color("✅ 所有测试通过", "green")
        return True

    def build_package(self) -> bool:
        """构建包"""
        if self.config.skip_build:
            self.logger.info("跳过包构建")
            return True

        print_section("构建包")

        # 清理旧的构建文件
        print_subsection("清理旧的构建文件")
        build_dir = os.path.join(self.config.project_dir, "build")
        dist_dir = os.path.join(self.config.project_dir, self.config.build_dir)

        if os.path.exists(build_dir):
            import shutil

            shutil.rmtree(build_dir)
            self.logger.info(f"删除build目录: {build_dir}")

        if os.path.exists(dist_dir):
            import shutil

            shutil.rmtree(dist_dir)
            self.logger.info(f"删除dist目录: {dist_dir}")

        # 构建包
        print_subsection("使用setuptools构建包")
        cmd = ["uv", "run", "python", "-m", "build"]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("包构建失败")
            print_color("❌ 包构建失败", "red")
            return False

        # 检查构建产物
        if not os.path.exists(dist_dir):
            self.logger.error("构建产物目录不存在")
            print_color("❌ 构建产物目录不存在", "red")
            return False

        # 列出构建产物
        print_subsection("构建产物")
        build_artifacts = os.listdir(dist_dir)
        for artifact in build_artifacts:
            artifact_path = os.path.join(dist_dir, artifact)
            file_size = os.path.getsize(artifact_path)
            self.logger.info(f"构建产物: {artifact} ({file_size} bytes)")
            print_color(f"  📦 {artifact} ({file_size} bytes)", "blue")

        print_color("✅ 包构建成功", "green")
        return True

    def publish_package(self) -> bool:
        """发布包到PyPI"""
        if self.config.skip_publish:
            self.logger.info("跳过包发布")
            return True

        print_section("发布包")

        # 选择发布目标
        if self.config.use_test_pypi:
            index_url = self.config.test_pypi_index_url
            repository_name = "testpypi"
            print_subsection("发布到TestPyPI")
        else:
            index_url = self.config.pypi_index_url
            repository_name = "pypi"
            print_subsection("发布到PyPI")

        # 检查是否为试运行
        if self.config.dry_run:
            self.logger.info("试运行模式，跳过实际发布")
            print_color("⚠️ 试运行模式，跳过实际发布", "yellow")
            return True

        # 发布包
        print_subsection("使用twine发布包")
        dist_dir = os.path.join(self.config.project_dir, self.config.build_dir)

        # 检查twine是否安装
        if not self._command_exists("twine"):
            self.logger.info("安装twine")
            print_subsection("安装twine")
            cmd = ["uv", "pip", "install", "twine"]
            success, _ = self._run_command(cmd, cwd=self.config.project_dir, quiet=True)
            if not success:
                self.logger.error("twine安装失败")
                print_color("❌ twine安装失败", "red")
                return False

        # 使用twine上传
        cmd = ["twine", "upload", "--repository-url", index_url, dist_dir + "/*"]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("包发布失败")
            print_color("❌ 包发布失败", "red")
            return False

        print_color(f"✅ 包成功发布到{repository_name}", "green")
        return True

    def manage_git_tags(self) -> bool:
        """管理Git标签"""
        if self.config.skip_git:
            self.logger.info("跳过Git标签管理")
            return True

        print_section("Git标签管理")

        # 检查Git仓库状态
        print_subsection("检查Git仓库状态")
        cmd = ["git", "status", "--porcelain"]
        success, output = self._run_command(
            cmd, cwd=self.config.project_dir, quiet=True
        )
        if not success:
            self.logger.warning("无法检查Git仓库状态")
            print_color("⚠️ 无法检查Git仓库状态", "yellow")
            return True

        if output.strip():
            self.logger.warning("Git仓库有未提交的更改")
            print_color("⚠️ Git仓库有未提交的更改，建议先提交更改", "yellow")
            if not self.config.dry_run:
                response = input("是否继续？(y/N): ")
                if response.lower() != "y":
                    self.logger.info("用户取消操作")
                    return False

        # 创建Git标签
        if self.config.create_git_tag:
            tag_name = f"v{self.current_version}"
            print_subsection(f"创建Git标签: {tag_name}")

            # 检查标签是否已存在
            cmd = ["git", "tag", "-l", tag_name]
            success, output = self._run_command(
                cmd, cwd=self.config.project_dir, quiet=True
            )
            if success and output.strip():
                self.logger.warning(f"Git标签已存在: {tag_name}")
                print_color(f"⚠️ Git标签已存在: {tag_name}", "yellow")
                if not self.config.dry_run:
                    response = input("是否删除现有标签并重新创建？(y/N): ")
                    if response.lower() == "y":
                        cmd = ["git", "tag", "-d", tag_name]
                        self._run_command(cmd, cwd=self.config.project_dir)
                    else:
                        return True

            # 创建标签
            cmd = ["git", "tag", "-a", tag_name, "-m", f"Release version {tag_name}"]
            if self.config.dry_run:
                self.logger.info(f"试运行: 创建Git标签 {tag_name}")
                print_color(f"🔍 试运行: 创建Git标签 {tag_name}", "yellow")
            else:
                success, _ = self._run_command(cmd, cwd=self.config.project_dir)
                if not success:
                    self.logger.error("Git标签创建失败")
                    print_color("❌ Git标签创建失败", "red")
                    return False
                print_color(f"✅ Git标签创建成功: {tag_name}", "green")

        # 推送Git标签
        if self.config.push_git_tag and self.config.create_git_tag:
            tag_name = f"v{self.current_version}"
            print_subsection(f"推送Git标签: {tag_name}")

            if self.config.dry_run:
                self.logger.info(f"试运行: 推送Git标签 {tag_name}")
                print_color(f"🔍 试运行: 推送Git标签 {tag_name}", "yellow")
            else:
                cmd = ["git", "push", "origin", tag_name]
                success, _ = self._run_command(cmd, cwd=self.config.project_dir)
                if not success:
                    self.logger.error("Git标签推送失败")
                    print_color("❌ Git标签推送失败", "red")
                    return False
                print_color(f"✅ Git标签推送成功: {tag_name}", "green")

        print_color("✅ Git标签管理完成", "green")
        return True

    def run(self) -> bool:
        """运行完整CD流程"""
        self.logger.info("开始CD流程")
        start_time = time.time()

        # 显示当前版本
        print_section("部署信息")
        print_color(f"项目目录: {self.config.project_dir}", "blue")
        print_color(f"当前版本: {self.current_version}", "blue")

        # 版本更新
        if self.config.version_bump:
            print_subsection(f"更新版本号: {self.config.version_bump}")
            self.current_version = self._bump_version(self.config.version_bump)
            print_color(f"新版本: {self.current_version}", "blue")

        # 运行各个阶段
        stages = [
            ("环境检查", self.check_environment),
            ("代码检查", self.run_checks),
            ("测试执行", self.run_tests),
            ("包构建", self.build_package),
            ("Git标签管理", self.manage_git_tags),
            ("包发布", self.publish_package),
        ]

        all_success = True
        for stage_name, stage_func in stages:
            self.logger.info(f"开始{stage_name}")
            if not stage_func():
                all_success = False
                self.logger.warning(f"{stage_name}失败")
                self.logger.info("停止CD流程")
                break
            self.logger.info(f"{stage_name}完成")

        # 总结
        print_section("CD流程总结结果")
        duration = time.time() - start_time

        if all_success:
            self.logger.info("所有CD步骤通过")
            print_color("🎉 所有CD步骤通过!", "green")
            print_color(f"📦 版本: {self.current_version}", "blue")
            print_color(f"⏱️ 总耗时: {duration:.2f}秒", "blue")
        else:
            self.logger.error("部分CD步骤失败")
            print_color("❌ 部分CD步骤失败!", "red")
            print_color(f"⏱️ 总耗时: {duration:.2f}秒", "blue")

        return all_success


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="ConsensusWeaverAgent CD脚本 - 持续部署自动化"
    )

    # 配置文件
    parser.add_argument("--config", type=str, help="配置文件路径")

    # 环境配置
    parser.add_argument(
        "--python-version",
        type=str,
        default=DEFAULT_CONFIG["PYTHON_VERSION"],
        help="Python版本",
    )
    parser.add_argument(
        "--uv-version", type=str, default=DEFAULT_CONFIG["UV_VERSION"], help="uv版本"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=DEFAULT_CONFIG["PROJECT_DIR"],
        help="项目目录",
    )

    # 跳过选项
    parser.add_argument("--skip-checks", action="store_true", help="跳过代码检查")
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试")
    parser.add_argument("--skip-build", action="store_true", help="跳过包构建")
    parser.add_argument("--skip-publish", action="store_true", help="跳过包发布")
    parser.add_argument("--skip-git", action="store_true", help="跳过Git操作")

    # 版本管理
    parser.add_argument(
        "--version-bump",
        choices=["major", "minor", "patch"],
        help="更新版本号 (major/minor/patch)",
    )

    # PyPI配置
    parser.add_argument(
        "--use-test-pypi", action="store_true", help="发布到TestPyPI而非PyPI"
    )

    # Git配置
    parser.add_argument("--create-git-tag", action="store_true", help="创建Git标签")
    parser.add_argument(
        "--push-git-tag", action="store_true", help="推送Git标签到远程仓库"
    )

    # 其他选项
    parser.add_argument(
        "--dry-run", action="store_true", help="试运行模式，不执行实际操作"
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="日志级别",
    )

    return parser.parse_args()


def main() -> int:
    """主函数"""
    args = parse_args()

    # 创建配置
    config = CDConfig(
        python_version=args.python_version,
        uv_version=args.uv_version,
        project_dir=args.project_dir,
        pypi_index_url=DEFAULT_CONFIG["PYPI_INDEX_URL"],
        test_pypi_index_url=DEFAULT_CONFIG["TEST_PYPI_INDEX_URL"],
        build_dir=DEFAULT_CONFIG["BUILD_DIR"],
        log_level=args.log_level,
        config_file=args.config,
        skip_checks=args.skip_checks,
        skip_tests=args.skip_tests,
        skip_build=args.skip_build,
        skip_publish=args.skip_publish,
        skip_git=args.skip_git,
        use_test_pypi=args.use_test_pypi,
        dry_run=args.dry_run,
        version_bump=args.version_bump,
        create_git_tag=args.create_git_tag,
        push_git_tag=args.push_git_tag,
    )

    # 创建CD实例并运行
    cd = CD(config)
    success = cd.run()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
ConsensusWeaverAgent CI/CD脚本

统一的持续集成和持续部署脚本，支持跨平台运行。
整合了原有的ci.py和cd.py功能，消除代码冗余，提供统一的配置和执行接口。

功能模块：
- CI（持续集成）：环境准备、依赖安装、代码检查、测试执行、安全检查
- CD（持续部署）：版本管理、代码检查、测试、构建、发布、Git标签管理

执行模式：
- ci: 仅执行CI流程
- cd: 仅执行CD流程
- all: 执行完整的CI/CD流程（默认）

重要说明：
- 默认情况下，CD流程会跳过发布到PyPI的步骤
- 如需发布到PyPI，请使用 --publish 参数显式启用
- 发布功能需要配置PyPI凭据（可通过 ~/.pypirc 或环境变量配置）
"""

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from typing import List, Optional, Tuple

DEFAULT_CONFIG = {
    "PYTHON_VERSION": "3.12",
    "UV_VERSION": "0.9.0",
    "PROJECT_DIR": os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "TEST_RESULTS_FILE": "test-results.xml",
    "SECURITY_REPORT_FILE": "security-report.json",
    "UV_INDEX_URL": "https://pypi.org/simple",
    "RUFF_OUTPUT_FORMAT": "github",
    "MYPY_STRICT": "false",
    "PYTEST_VERBOSE": "true",
    "PYTEST_TB_STYLE": "short",
    "PYPI_INDEX_URL": "https://upload.pypi.org/legacy/",
    "TEST_PYPI_INDEX_URL": "https://test.pypi.org/legacy/",
    "BUILD_DIR": "dist",
    "COVERAGE_ENABLED": "true",
    "COVERAGE_THRESHOLD": "75",
}


class Colors:
    """终端颜色定义，支持跨平台"""

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
class CICDConfig:
    """统一的CI/CD配置类"""

    python_version: str
    uv_version: str
    project_dir: str
    test_results_file: str
    security_report_file: str
    uv_index_url: str
    ruff_output_format: str
    mypy_strict: bool
    pytest_verbose: bool
    pytest_tb_style: str
    pypi_index_url: str
    test_pypi_index_url: str
    build_dir: str
    log_level: str
    config_file: Optional[str]
    skip_env_prep: bool
    skip_deps: bool
    skip_format: bool
    skip_mypy: bool
    skip_tests: bool
    skip_security: bool
    skip_checks: bool
    skip_build: bool
    skip_publish: bool
    skip_git: bool
    upload_artifacts: bool
    use_test_pypi: bool
    dry_run: bool
    version_bump: Optional[str]
    create_git_tag: bool
    push_git_tag: bool
    coverage_enabled: bool
    coverage_threshold: int
    auto_fix: bool
    skip_nltk: bool
    pytest_k: Optional[str]
    skip_coverage: bool


class CICDError(Exception):
    """CI/CD执行错误"""

    pass


class CICD:
    """统一的CI/CD脚本主类"""

    def __init__(self, config: CICDConfig):
        self.config = config
        self.logger = self._setup_logger()
        self._setup_environment()
        self.current_version = self._get_current_version()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("CICD")
        logger.setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO))

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        log_dir = os.path.join(self.config.project_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "cicd.log")
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
        os.environ["UV_INDEX_URL"] = self.config.uv_index_url

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
            raise CICDError(f"pyproject.toml不存在: {pyproject_path}")

        with open(pyproject_path, "rb") as f:
            data: dict[str, object] = tomllib.load(f)
            project_data = data.get("project")
            if not isinstance(project_data, dict):
                raise CICDError("pyproject.toml中缺少project配置")
            version = project_data.get("version")
            if not isinstance(version, str):
                raise CICDError("无法从pyproject.toml获取版本号")
            return version

    def _bump_version(self, bump_type: str) -> str:
        """更新版本号

        Args:
            bump_type: 版本更新类型 (major, minor, patch)

        Returns:
            新版本号
        """
        if bump_type not in ["major", "minor", "patch"]:
            raise CICDError(f"无效的版本更新类型: {bump_type}")

        parts = self.current_version.split(".")
        if len(parts) < 3:
            raise CICDError(f"无效的版本号格式: {self.current_version}")

        patch_part = parts[2]
        if ".dev" in patch_part:
            patch_part = patch_part.split(".dev")[0]

        try:
            version_parts = [int(parts[0]), int(parts[1]), int(patch_part)]
        except ValueError as e:
            raise CICDError(f"无效的版本号格式: {self.current_version}, 错误: {e}")

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

        pyproject_path = os.path.join(self.config.project_dir, "pyproject.toml")
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()

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

    def setup_environment(self) -> bool:
        """环境准备（CI功能）"""
        if self.config.skip_env_prep:
            self.logger.info("跳过环境准备")
            return True

        print_section("环境准备")

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

        version_cmd = [python_cmd, "--version"]
        result = subprocess.run(version_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            self.logger.error("无法获取Python版本")
            print_color("❌ 无法获取Python版本", "red")
            return False

        version_output = result.stdout.strip()
        self.logger.info(f"当前Python版本: {version_output}")
        print_color(f"ℹ️ 当前Python版本: {version_output}", "blue")

        if self.config.python_version not in version_output:
            self.logger.error(f"需要Python {self.config.python_version}或更高版本")
            print_color(f"❌ 需要Python {self.config.python_version}或更高版本", "red")
            return False

        print_color("✅ Python版本符合要求", "green")

        print_subsection("安装uv依赖管理工具")
        if self._command_exists("uv"):
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                current_version = result.stdout.strip()
                self.logger.info(f"uv已经安装: {current_version}")
                print_color(f"✅ uv已经安装: {current_version}", "green")
            else:
                self.logger.error("无法获取uv版本")
                print_color("⚠️ 无法获取uv版本，尝试重新安装", "yellow")
                cmd = [python_cmd, "-m", "pip", "install", "uv"]
                success, _ = self._run_command(cmd, quiet=True)
                if not success:
                    self.logger.error("uv安装失败")
                    print_color("❌ uv安装失败", "red")
                    return False
        else:
            cmd = [python_cmd, "-m", "pip", "install", "uv"]
            success, _ = self._run_command(cmd, quiet=True)
            if not success:
                self.logger.error("uv安装失败")
                print_color("❌ uv安装失败", "red")
                return False
            print_color("✅ uv安装成功", "green")

        print_color("✅ 环境准备完成", "green")
        return True

    def check_environment(self) -> bool:
        """检查部署环境（CD功能）"""
        print_section("检查部署环境")

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

        version_cmd = [python_cmd, "--version"]
        result = subprocess.run(version_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            self.logger.error("无法获取Python版本")
            print_color("❌ 无法获取Python版本", "red")
            return False

        version_output = result.stdout.strip()
        self.logger.info(f"当前Python版本: {version_output}")
        print_color(f"ℹ️ 当前Python版本: {version_output}", "blue")

        if self.config.python_version not in version_output:
            self.logger.error(f"需要Python {self.config.python_version}或更高版本")
            print_color(f"❌ 需要Python {self.config.python_version}或更高版本", "red")
            return False

        print_color("✅ Python版本符合要求", "green")

        print_subsection("检查uv依赖管理工具")
        if not self._command_exists("uv"):
            self.logger.error("uv未安装")
            print_color("❌ uv未安装", "red")
            return False

        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            uv_version = result.stdout.strip()
            self.logger.info(f"uv版本: {uv_version}")
            print_color(f"✅ uv已安装: {uv_version}", "green")
        else:
            self.logger.error("无法获取uv版本")
            print_color("❌ 无法获取uv版本", "red")
            return False

        print_subsection("检查Git版本控制")
        if not self._command_exists("git"):
            self.logger.warning("Git未安装，将跳过Git相关操作")
            print_color("⚠️ Git未安装，将跳过Git相关操作", "yellow")
            self.config.skip_git = True
        else:
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

    def install_dependencies(self) -> bool:
        """安装项目依赖（CI功能）"""
        if self.config.skip_deps:
            self.logger.info("跳过依赖安装")
            return True

        print_section("安装项目依赖")

        is_ci = os.environ.get("CI") == "true"

        if is_ci:
            cmd = ["uv", "pip", "install", "-e", ".", "--group", "dev", "--system"]
        else:
            cmd = ["uv", "pip", "install", "-e", ".[dev]"]

        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("项目依赖安装失败")
            print_color("❌ 项目依赖安装失败", "red")
            return False

        print_color("✅ 项目依赖安装成功", "green")
        return True

    def check_code_format(self) -> bool:
        """代码规范检查Linting（共享功能）"""
        if self.config.skip_format:
            self.logger.info("跳过代码规范检查")
            return True

        print_section("代码规范检查Linting")

        if self.config.auto_fix:
            print_subsection("使用ruff自动修复代码规范问题")
            print_subsection(
                "注意：自动修复只能解决部分问题（如未使用的导入、变量、导入排序等）"
            )
            cmd = ["uv", "run", "ruff", "check", "--fix", "."]
            success, output = self._run_command(cmd, cwd=self.config.project_dir)
            if not success:
                self.logger.error("代码规范规范修复失败")
                print_color("❌ 代码规范自动修复失败", "red")
                return False
            print_color("✅ 代码规范自动修复完成", "green")

        print_subsection("使用ruff检查代码规范")
        cmd = [
            "uv",
            "run",
            "ruff",
            "check",
            f"--output-format={self.config.ruff_output_format}",
            ".",
        ]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("代码规范检查失败")
            print_color("❌ 代码规范检查失败", "red")
            return False

        print_color("✅ 代码规范检查通过", "green")
        return True

    def format_code(self) -> bool:
        """代码格式化（CI功能）"""
        if self.config.skip_format:
            self.logger.info("跳过代码格式化")
            return True

        print_section("代码格式化（Formatting）")

        print_subsection("使用ruff格式化代码")
        cmd = ["uv", "run", "ruff", "format", "."]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("代码格式化失败")
            print_color("❌ 代码格式化失败", "red")
            return False

        print_color("✅ 代码格式化完成", "green")
        return True

    def type_check(self) -> bool:
        """类型检查（共享功能）"""
        if self.config.skip_mypy:
            self.logger.info("跳过类型检查")
            return True

        print_section("类型检查")

        print_subsection("使用mypy进行类型检查")

        original_pythonpath = os.environ.get("PYTHONPATH", "")
        src_path = os.path.abspath(os.path.join(self.config.project_dir, "src"))
        separator = ";" if os.name == "nt" else ":"
        os.environ["PYTHONPATH"] = src_path + separator + original_pythonpath

        try:
            cmd = [
                "uv",
                "run",
                "mypy",
                "--namespace-packages",
                "--ignore-missing-imports",
                "--follow-imports=skip",
            ]
            if self.config.mypy_strict:
                cmd.append("--strict")
            cmd.append("src/")

            success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        finally:
            os.environ["PYTHONPATH"] = original_pythonpath
        if not success:
            self.logger.error("类型检查失败")
            print_color("❌ 类型检查失败", "red")
            return False

        print_color("✅ 类型检查通过", "green")
        return True

    def run_checks(self) -> bool:
        """运行代码检查（CD功能）"""
        if self.config.skip_checks:
            self.logger.info("跳过代码检查")
            return True

        print_section("运行代码检查")

        print_subsection("使用ruff代码规范检查（Linting）")
        cmd = ["uv", "run", "ruff", "check", "--output-format=github", "."]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("代码规范检查失败")
            print_color("❌ 代码规范检查失败", "red")
            return False

        print_color("✅ 代码规范检查通过", "green")

        print_subsection("使用mypy进行类型检查")
        cmd = [
            "uv",
            "run",
            "mypy",
            "--namespace-packages",
            "--ignore-missing-imports",
            "--follow-imports=skip",
        ]
        if self.config.mypy_strict:
            cmd.append("--strict")
        cmd.append("src/")
        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("类型检查失败")
            print_color("❌ 类型检查失败", "red")
            return False

        print_color("✅ 类型检查通过", "green")
        print_color("✅ 所有代码检查通过", "green")
        return True

    def run_tests(self) -> bool:
        """运行测试（共享功能）"""
        if self.config.skip_tests:
            self.logger.info("跳过测试执行")
            return True

        print_section("运行测试")

        if not self.config.skip_nltk:
            print_subsection("下载NLTK数据")
            nltk_download_cmd = ["uv", "run", "python", "Scripts/download_nltk_data.py"]
            nltk_success, nltk_output = self._run_command(
                nltk_download_cmd, cwd=self.config.project_dir
            )
            if not nltk_success:
                self.logger.warning("NLTK数据下载失败，继续执行测试")
                print_color("⚠️ NLTK数据下载失败，继续执行测试", "yellow")
            else:
                print_color("✅ NLTK数据下载成功", "green")

        test_results_dir = os.path.join(
            self.config.project_dir, "reports", "test-results"
        )
        os.makedirs(test_results_dir, exist_ok=True)
        test_results_file = os.path.join(test_results_dir, "test-results.xml")

        print_subsection("使用pytest运行测试并生成报告")
        cmd = ["uv", "run", "pytest", "tests/"]
        cmd.extend(["-n", "auto"])
        if self.config.pytest_verbose:
            cmd.append("-v")
        if self.config.pytest_tb_style:
            cmd.append(f"--tb={self.config.pytest_tb_style}")
        cmd.extend(["--junitxml", test_results_file])

        if self.config.pytest_k:
            cmd.extend(["-k", self.config.pytest_k])

        if self.config.coverage_enabled and not self.config.skip_coverage:
            cmd.extend(
                [
                    "--cov=src",
                    "--cov-report=xml",
                    "--cov-report=html",
                    f"--cov-fail-under={self.config.coverage_threshold}",
                ]
            )

        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("测试执行失败")
            print_color("❌ 测试执行失败", "red")
            return False

        print_color("✅ 测试执行成功", "green")
        print_color(f"✅ 测试报告生成成功: {test_results_file}", "green")
        if self.config.coverage_enabled:
            print_color("✅ 覆盖率报告生成成功", "green")
        return True

    def generate_test_report(self) -> bool:
        """生成测试报告（CI功能）"""
        if self.config.skip_tests:
            self.logger.info("跳过测试报告生成")
            return True

        print_section("生成测试报告")

        test_results_dir = os.path.join(
            self.config.project_dir, "reports", "test-results"
        )
        test_results_file = os.path.join(test_results_dir, "test-results.xml")

        if os.path.exists(test_results_file):
            print_subsection("测试报告已存在")
            print_color(f"✅ 测试报告已存在: {test_results_file}", "green")
            return True
        else:
            print_subsection("生成JUnit测试报告")
            os.makedirs(test_results_dir, exist_ok=True)
            cmd = [
                "uv",
                "run",
                "pytest",
                "tests/",
                "--junitxml",
                test_results_file,
                "-n",
                "auto",
            ]
            success, _ = self._run_command(cmd, cwd=self.config.project_dir, quiet=True)
            if not success:
                self.logger.error("测试报告生成失败")
                print_color("❌ 测试报告生成失败", "red")
                return False

            print_color(f"✅ 测试报告生成成功: {test_results_file}", "green")
            return True

    def run_security_check(self) -> bool:
        """运行安全检查（CI功能）"""
        if self.config.skip_security:
            self.logger.info("跳过安全检查")
            return True

        print_section("安全检查")

        print_subsection("安装安全检查工具bandit")
        cmd = ["uv", "pip", "install", "bandit"]
        install_success, _ = self._run_command(
            cmd, cwd=self.config.project_dir, quiet=True
        )
        if not install_success:
            self.logger.warning("bandit安装失败，跳过安全检查")
            print_color("⚠️ bandit安装失败，跳过安全检查", "yellow")
            return True

        security_dir = os.path.join(self.config.project_dir, "reports", "security")
        os.makedirs(security_dir, exist_ok=True)

        print_subsection("使用bandit进行安全检查")
        security_report_file = os.path.join(security_dir, "security-report.json")
        cmd = [
            "uv",
            "run",
            "bandit",
            "-r",
            "src/",
            "-f",
            "json",
            "-o",
            security_report_file,
            "-ll",
        ]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir, quiet=True)
        if not success:
            self.logger.warning("安全检查发现问题")
            print_color("⚠️ 安全检查发现问题，请查看报告", "yellow")
        else:
            print_color(f"✅ 安全检查完成: {security_report_file}", "green")

        return True

    def build_package(self) -> bool:
        """构建包（CD功能）"""
        if self.config.skip_build:
            self.logger.info("跳过包构建")
            return True

        print_section("构建包")

        print_subsection("清理旧的构建文件")
        build_dir = os.path.join(self.config.project_dir, "build")
        dist_dir = os.path.join(self.config.project_dir, self.config.build_dir)

        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
            self.logger.info(f"删除build目录: {build_dir}")

        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir)
            self.logger.info(f"删除dist目录: {dist_dir}")

        print_subsection("使用setuptools构建包")
        cmd = ["uv", "run", "python", "-m", "build"]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("包构建失败")
            print_color("❌ 包构建失败", "red")
            return False

        if not os.path.exists(dist_dir):
            self.logger.error("构建产物目录不存在")
            print_color("❌ 构建产物目录不存在", "red")
            return False

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
        """发布包到PyPI（CD功能）"""
        if self.config.skip_publish:
            self.logger.info("跳过包发布")
            return True

        print_section("发布包")

        if self.config.use_test_pypi:
            index_url = self.config.test_pypi_index_url
            repository_name = "testpypi"
            print_subsection("发布到TestPyPI")
        else:
            index_url = self.config.pypi_index_url
            repository_name = "pypi"
            print_subsection("发布到PyPI")

        if self.config.dry_run:
            self.logger.info("试运行模式，跳过实际发布")
            print_color("⚠️ 试运行模式，跳过实际发布", "yellow")
            return True

        print_subsection("使用twine发布包")
        dist_dir = os.path.join(self.config.project_dir, self.config.build_dir)

        if not self._command_exists("twine"):
            self.logger.info("安装twine")
            print_subsection("安装twine")
            cmd = ["uv", "pip", "install", "twine"]
            success, _ = self._run_command(cmd, cwd=self.config.project_dir, quiet=True)
            if not success:
                self.logger.error("twine安装失败")
                print_color("❌ twine安装失败", "red")
                return False

        cmd = ["twine", "upload", "--repository-url", index_url, dist_dir + "/*"]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("包发布失败")
            print_color("❌ 包发布失败", "red")
            return False

        print_color(f"✅ 包成功发布到{repository_name}", "green")
        return True

    def manage_git_tags(self) -> bool:
        """管理Git标签（CD功能）"""
        if self.config.skip_git:
            self.logger.info("跳过Git标签管理")
            return True

        print_section("Git标签管理")

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

        if self.config.create_git_tag:
            tag_name = f"v{self.current_version}"
            print_subsection(f"创建Git标签: {tag_name}")

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

    def run_ci(self) -> bool:
        """运行完整CI流程"""
        self.logger.info("开始CI流程")
        start_time = time.time()

        stages = [
            ("环境准备", self.setup_environment),
            ("依赖安装", self.install_dependencies),
            ("代码规范检查", self.check_code_format),
            ("代码格式化", self.format_code),
            ("类型检查", self.type_check),
            ("测试执行", self.run_tests),
            ("测试报告生成", self.generate_test_report),
            ("安全检查", self.run_security_check),
        ]

        all_success = True
        for stage_name, stage_func in stages:
            self.logger.info(f"开始{stage_name}")
            if not stage_func():
                all_success = False
                self.logger.warning(f"{stage_name}失败")
            self.logger.info(f"{stage_name}完成")

        print_section("CI流程总结")
        duration = time.time() - start_time

        if all_success:
            self.logger.info("所有CI步骤通过")
            print_color("🎉 所有CI步骤通过!", "green")
            print_color(f"⏱️ 总耗时: {duration:.2f}秒", "blue")
        else:
            self.logger.error("部分CI步骤失败")
            print_color("❌ 部分CI步骤失败!", "red")
            print_color(f"⏱️ 总耗时: {duration:.2f}秒", "blue")

        return all_success

    def run_cd(self) -> bool:
        """运行完整CD流程"""
        self.logger.info("开始CD流程")
        start_time = time.time()

        if self.config.version_bump:
            print_section("版本管理")
            new_version = self._bump_version(self.config.version_bump)
            self.current_version = new_version

        stages = [
            ("环境检查", self.check_environment),
            ("代码检查", self.run_checks),
            ("测试执行", self.run_tests),
            ("包构建", self.build_package),
            ("包发布", self.publish_package),
            ("Git标签管理", self.manage_git_tags),
        ]

        all_success = True
        for stage_name, stage_func in stages:
            self.logger.info(f"开始{stage_name}")
            if not stage_func():
                all_success = False
                self.logger.warning(f"{stage_name}失败")
            self.logger.info(f"{stage_name}完成")

        print_section("CD流程总结")
        duration = time.time() - start_time

        if all_success:
            self.logger.info("所有CD步骤通过")
            print_color("🎉 所有CD步骤通过!", "green")
            print_color(f"⏱️ 总耗时: {duration:.2f}秒", "blue")
        else:
            self.logger.error("部分CD步骤失败")
            print_color("❌ 部分CD步骤失败!", "red")
            print_color(f"⏱️ 总耗时: {duration:.2f}秒", "blue")

        return all_success

    def run(self) -> bool:
        """运行完整CI/CD流程"""
        self.logger.info("开始CI/CD流程")
        start_time = time.time()

        if self.config.version_bump:
            print_section("版本管理")
            new_version = self._bump_version(self.config.version_bump)
            self.current_version = new_version

        stages = [
            ("环境准备", self.setup_environment),
            ("依赖安装", self.install_dependencies),
            ("代码规范检查", self.check_code_format),
            ("代码格式化", self.format_code),
            ("类型检查", self.type_check),
            ("测试执行", self.run_tests),
            ("测试报告生成", self.generate_test_report),
            ("安全检查", self.run_security_check),
            ("环境检查", self.check_environment),
            ("代码检查", self.run_checks),
            ("包构建", self.build_package),
            ("包发布", self.publish_package),
            ("Git标签管理", self.manage_git_tags),
        ]

        all_success = True
        for stage_name, stage_func in stages:
            self.logger.info(f"开始{stage_name}")
            if not stage_func():
                all_success = False
                self.logger.warning(f"{stage_name}失败")
            self.logger.info(f"{stage_name}完成")

        print_section("CI/CD流程总结")
        duration = time.time() - start_time

        if all_success:
            self.logger.info("所有CI/CD步骤通过")
            print_color("🎉 所有CI/CD步骤通过!", "green")
            print_color(f"⏱️ 总耗时: {duration:.2f}秒", "blue")
        else:
            self.logger.error("部分CI/CD步骤失败")
            print_color("❌ 部分CI/CD步骤失败!", "red")
            print_color(f"⏱️ 总耗时: {duration:.2f}秒", "blue")

        return all_success


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="ConsensusWeaverAgent CI/CD脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
执行模式：
  ci    仅执行CI流程（代码检查、测试、安全检查）
  cd    仅执行CD流程（版本管理、构建、发布）
  all   执行完整的CI/CD流程（默认）

示例：
  python cicd.py --mode ci              # 仅执行CI流程
  python cicd.py --mode cd --version-bump patch  # 执行CD流程并更新patch版本
  python cicd.py --mode all --dry-run   # 试运行完整CI/CD流程
  python cicd.py --mode cd --publish    # 执行CD流程并发布到PyPI
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["ci", "cd", "all"],
        default="all",
        help="执行模式：ci（仅CI）、cd（仅CD）、all（完整CI/CD）",
    )

    parser.add_argument("--config", type=str, help="配置文件路径")

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

    parser.add_argument("--skip-env-prep", action="store_true", help="跳过环境准备")
    parser.add_argument("--skip-deps", action="store_true", help="跳过依赖安装")
    parser.add_argument(
        "--skip-format", action="store_true", help="跳过代码规范检查和格式化"
    )
    parser.add_argument("--skip-mypy", action="store_true", help="跳过类型检查")
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试执行")
    parser.add_argument("--skip-nltk", action="store_true", help="跳过NLTK数据下载")
    parser.add_argument("--pytest-k", type=str, help="pytest -k参数（过滤测试）")
    parser.add_argument("--skip-coverage", action="store_true", help="跳过覆盖率检查")
    parser.add_argument("--skip-security", action="store_true", help="跳过安全检查")
    parser.add_argument("--skip-checks", action="store_true", help="跳过代码检查（CD）")
    parser.add_argument("--skip-build", action="store_true", help="跳过包构建")
    parser.add_argument("--skip-publish", action="store_true", help="跳过包发布")
    parser.add_argument(
        "--publish", action="store_true", help="启用包发布到PyPI（默认跳过）"
    )
    parser.add_argument("--skip-git", action="store_true", help="跳过Git标签管理")

    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="日志级别",
    )

    parser.add_argument(
        "--upload-artifacts", action="store_true", help="上传测试报告（仅CI环境有效）"
    )
    parser.add_argument(
        "--mypy-strict", action="store_true", help="使用严格的类型检查模式"
    )
    parser.add_argument(
        "--no-mypy-strict", action="store_true", help="不使用严格的类型检查模式"
    )

    parser.add_argument(
        "--no-auto-fix",
        action="store_true",
        help="禁用自动修复代码格式问题（本地CI默认启用）",
    )

    parser.add_argument(
        "--use-test-pypi", action="store_true", help="发布到TestPyPI而非PyPI"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="试运行模式，不实际执行发布操作"
    )
    parser.add_argument(
        "--version-bump",
        choices=["major", "minor", "patch"],
        help="版本更新类型：major（主版本）、minor（次版本）、patch（补丁版本）",
    )
    parser.add_argument("--create-git-tag", action="store_true", help="创建Git版本标签")
    parser.add_argument(
        "--push-git-tag", action="store_true", help="推送Git版本标签到远程仓库"
    )

    return parser.parse_args()


def main() -> int:
    """主函数"""
    args = parse_args()

    mypy_strict = args.mypy_strict
    if args.no_mypy_strict:
        mypy_strict = False

    skip_publish = not args.publish

    auto_fix = not args.no_auto_fix

    config = CICDConfig(
        python_version=args.python_version,
        uv_version=args.uv_version,
        project_dir=args.project_dir,
        test_results_file=DEFAULT_CONFIG["TEST_RESULTS_FILE"],
        security_report_file=DEFAULT_CONFIG["SECURITY_REPORT_FILE"],
        uv_index_url=DEFAULT_CONFIG["UV_INDEX_URL"],
        ruff_output_format=DEFAULT_CONFIG["RUFF_OUTPUT_FORMAT"],
        mypy_strict=mypy_strict,
        pytest_verbose=DEFAULT_CONFIG["PYTEST_VERBOSE"] == "true",
        pytest_tb_style=DEFAULT_CONFIG["PYTEST_TB_STYLE"],
        pypi_index_url=DEFAULT_CONFIG["PYPI_INDEX_URL"],
        test_pypi_index_url=DEFAULT_CONFIG["TEST_PYPI_INDEX_URL"],
        build_dir=DEFAULT_CONFIG["BUILD_DIR"],
        log_level=args.log_level,
        config_file=args.config,
        skip_env_prep=args.skip_env_prep,
        skip_deps=args.skip_deps,
        skip_format=args.skip_format,
        skip_mypy=args.skip_mypy,
        skip_tests=args.skip_tests,
        skip_security=args.skip_security,
        skip_checks=args.skip_checks,
        skip_build=args.skip_build,
        skip_publish=skip_publish,
        skip_git=args.skip_git,
        upload_artifacts=args.upload_artifacts,
        use_test_pypi=args.use_test_pypi,
        dry_run=args.dry_run,
        version_bump=args.version_bump,
        create_git_tag=args.create_git_tag,
        push_git_tag=args.push_git_tag,
        coverage_enabled=DEFAULT_CONFIG["COVERAGE_ENABLED"] == "true",
        coverage_threshold=int(DEFAULT_CONFIG["COVERAGE_THRESHOLD"]),
        auto_fix=auto_fix,
        skip_nltk=args.skip_nltk,
        pytest_k=args.pytest_k,
        skip_coverage=args.skip_coverage,
    )

    cicd = CICD(config)

    if args.mode == "ci":
        success = cicd.run_ci()
    elif args.mode == "cd":
        success = cicd.run_cd()
    else:
        success = cicd.run()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

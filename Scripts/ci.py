#!/usr/bin/env python3
"""
ConsensusWeaverAgent CI脚本

基于GitHub Actions的ci.yml文件实现的本地CI脚本，支持跨平台运行。
实现代码检查、测试执行、构建流程等核心环节。
"""

import argparse
import configparser
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# 配置默认值
DEFAULT_CONFIG = {
    "PYTHON_VERSION": "3.12",
    "UV_VERSION": "0.9.0",
    "PROJECT_DIR": os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "TEST_RESULTS_FILE": "test-results.xml",
    "SECURITY_REPORT_FILE": "security-report.json",
    "UV_INDEX_URL": "https://pypi.org/simple",
    "RUFF_OUTPUT_FORMAT": "github",
    "MYPY_STRICT": "true",
    "PYTEST_VERBOSE": "true",
    "PYTEST_TB_STYLE": "short",
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
class CIConfig:
    """CI配置类"""

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
    log_level: str
    config_file: Optional[str]
    skip_env_prep: bool
    skip_deps: bool
    skip_format: bool
    skip_mypy: bool
    skip_tests: bool
    skip_security: bool
    upload_artifacts: bool


class CIError(Exception):
    """CI执行错误"""

    pass


class CI:
    """CI脚本主类"""

    def __init__(self, config: CIConfig):
        self.config = config
        self.logger = self._setup_logger()
        self._setup_environment()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("CI")
        logger.setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO))

        # 控制台日志
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 文件日志
        log_file = os.path.join(self.config.project_dir, "ci.log")
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

    def setup_environment(self) -> bool:
        """环境准备"""
        if self.config.skip_env_prep:
            self.logger.info("跳过环境准备")
            return True

        print_section("环境准备")

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

        # 安装uv
        print_subsection("安装uv依赖管理工具")
        # 检查uv是否已经安装
        if self._command_exists("uv"):
            # 获取当前uv版本
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                current_version = result.stdout.strip()
                self.logger.info(f"uv已经安装: {current_version}")
                print_color(f"✅ uv已经安装: {current_version}", "green")
            else:
                self.logger.error("无法获取uv版本")
                print_color("⚠️ 无法获取uv版本，尝试重新安装", "yellow")
                # 尝试安装uv
                cmd = [python_cmd, "-m", "pip", "install", "uv"]
                success, _ = self._run_command(cmd, quiet=True)
                if not success:
                    self.logger.error("uv安装失败")
                    print_color("❌ uv安装失败", "red")
                    return False
        else:
            # 安装uv
            cmd = [python_cmd, "-m", "pip", "install", "uv"]
            success, _ = self._run_command(cmd, quiet=True)
            if not success:
                self.logger.error("uv安装失败")
                print_color("❌ uv安装失败", "red")
                return False
            print_color("✅ uv安装成功", "green")

        print_color("✅ 环境准备完成", "green")
        return True

    def install_dependencies(self) -> bool:
        """安装项目依赖"""
        if self.config.skip_deps:
            self.logger.info("跳过依赖安装")
            return True

        print_section("安装项目依赖")

        # 检查是否在CI环境
        is_ci = os.environ.get("CI") == "true"

        # 根据环境选择命令
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
        """代码格式检查"""
        if self.config.skip_format:
            self.logger.info("跳过关代码格式检查")
            return True

        print_section("代码格式检查")

        # 使用ruff检查代码格式
        print_subsection("使用ruff检查代码格式")
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
            self.logger.error("代码格式检查失败")
            print_color("❌ 代码格式检查失败", "red")
            return False

        print_color("✅ 代码格式检查通过", "green")
        return True

    def format_code(self) -> bool:
        """代码格式化"""
        if self.config.skip_format:
            self.logger.info("跳过代码格式化")
            return True

        print_section("代码格式化")

        # 使用ruff格式化代码
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
        """类型检查"""
        if self.config.skip_mypy:
            self.logger.info("跳过类型检查")
            return True

        print_section("类型检查")

        # 使用mypy进行类型检查
        print_subsection("使用mypy进行类型检查")

        # 临时修改PYTHONPATH，确保正确的模块搜索顺序
        original_pythonpath = os.environ.get("PYTHONPATH", "")
        src_path = os.path.abspath(os.path.join(self.config.project_dir, "src"))
        # 设置PYTHONPATH，Windows使用分号，其他系统使用冒号
        separator = ";" if os.name == "nt" else ":"
        os.environ["PYTHONPATH"] = src_path + separator + original_pythonpath

        try:
            cmd = [
                "uv",
                "run",
                "mypy",
                "--namespace-packages",  # 使用命名空间包模式，避免模块名冲突
                "--ignore-missing-imports",  # 忽略缺失的导入
                "--follow-imports=skip",  # 不跟随导入，避免模块名冲突
            ]
            # 根据配置决定是否使用严格模式
            if self.config.mypy_strict:
                cmd.append("--strict")
            cmd.append("src/")  # 只检查src目录下的文件

            success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        finally:
            # 恢复原始PYTHONPATH
            os.environ["PYTHONPATH"] = original_pythonpath
        if not success:
            self.logger.error("类型检查失败")
            print_color("❌ 类型检查失败", "red")
            return False

        print_color("✅ 类型检查通过", "green")
        return True

    def run_tests(self) -> bool:
        """运行测试"""
        if self.config.skip_tests:
            self.logger.info("跳过测试执行")
            return True

        print_section("运行测试")

        # 使用pytest运行测试
        print_subsection("使用pytest运行测试")
        cmd = ["uv", "run", "pytest", "tests/"]
        # 添加并行测试支持，自动使用所有可用CPU核心
        cmd.extend(["-n", "auto"])
        if self.config.pytest_verbose:
            cmd.append("-v")
        if self.config.pytest_tb_style:
            cmd.append(f"--tb={self.config.pytest_tb_style}")

        success, _ = self._run_command(cmd, cwd=self.config.project_dir)
        if not success:
            self.logger.error("测试执行失败")
            print_color("❌ 测试执行失败", "red")
            return False

        print_color("✅ 测试执行成功", "green")
        return True

    def generate_test_report(self) -> bool:
        """生成测试报告"""
        if self.config.skip_tests:
            self.logger.info("跳过测试报告生成")
            return True

        print_section("生成测试报告")

        # 生成JUnit测试报告
        print_subsection("生成JUnit测试报告")
        cmd = [
            "uv",
            "run",
            "pytest",
            "tests/",
            "--junitxml",
            self.config.test_results_file,
        ]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir, quiet=True)
        if not success:
            self.logger.error("测试报告生成失败")
            print_color("❌ 测试报告生成失败", "red")
            return False

        print_color(f"✅ 测试报告生成成功: {self.config.test_results_file}", "green")
        return True

    def run_security_check(self) -> bool:
        """运行安全检查"""
        if self.config.skip_security:
            self.logger.info("跳过安全检查")
            return True

        print_section("安全检查")

        # 安装bandit
        print_subsection("安装安全检查工具bandit")
        cmd = ["uv", "pip", "install", "bandit"]
        install_success, _ = self._run_command(
            cmd, cwd=self.config.project_dir, quiet=True
        )
        if not install_success:
            self.logger.warning("bandit安装失败，跳过安全检查")
            print_color("⚠️ bandit安装失败，跳过安全检查", "yellow")
            return True

        # 运行安全检查
        print_subsection("使用bandit进行安全检查")
        cmd = [
            "uv",
            "run",
            "bandit",
            "-r",
            "src/",
            "-f",
            "json",
            "-o",
            self.config.security_report_file,
        ]
        success, _ = self._run_command(cmd, cwd=self.config.project_dir, quiet=True)
        if not success:
            self.logger.warning("安全检查发现问题")
            print_color("⚠️ 安全检查发现问题，请查看报告", "yellow")
        else:
            print_color(f"✅ 安全检查完成: {self.config.security_report_file}", "green")

        return True

    def run(self) -> bool:
        """运行完整CI流程"""
        self.logger.info("开始CI流程")
        start_time = time.time()

        # 运行各个阶段
        stages = [
            ("环境准备", self.setup_environment),
            ("依赖安装", self.install_dependencies),
            ("代码格式检查", self.check_code_format),
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

        # 总结
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


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="ConsensusWeaverAgent CI脚本")

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
    parser.add_argument("--skip-env-prep", action="store_true", help="跳过环境准备")
    parser.add_argument("--skip-deps", action="store_true", help="跳过依赖安装")
    parser.add_argument(
        "--skip-format", action="store_true", help="跳过代码格式检查和格式化"
    )
    parser.add_argument("--skip-mypy", action="store_true", help="跳过类型检查")
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试执行")
    parser.add_argument("--skip-security", action="store_true", help="跳过安全检查")

    # 日志配置
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="日志级别",
    )

    # 其他选项
    parser.add_argument(
        "--upload-artifacts", action="store_true", help="上传测试报告（仅CI环境有效）"
    )
    parser.add_argument(
        "--mypy-strict", action="store_true", help="使用严格的类型检查模式"
    )
    parser.add_argument(
        "--no-mypy-strict", action="store_true", help="不使用严格的类型检查模式"
    )

    return parser.parse_args()


def load_config(config_file: Optional[str]) -> Dict[str, str]:
    """加载配置文件"""
    config = DEFAULT_CONFIG.copy()

    if config_file and os.path.exists(config_file):
        parser = configparser.ConfigParser()
        parser.read(config_file)

        if "CI" in parser:
            config.update(parser["CI"])

    return config


def create_config(args: argparse.Namespace) -> CIConfig:
    """创建CI配置对象"""
    # 加载配置文件
    config_dict = load_config(args.config)

    # 命令行参数覆盖配置文件
    config_dict["PYTHON_VERSION"] = args.python_version
    config_dict["UV_VERSION"] = args.uv_version
    config_dict["PROJECT_DIR"] = args.project_dir

    # 处理mypy严格模式参数
    if hasattr(args, "mypy_strict") and args.mypy_strict:
        config_dict["MYPY_STRICT"] = "true"
    if hasattr(args, "no_mypy_strict") and args.no_mypy_strict:
        config_dict["MYPY_STRICT"] = "false"

    return CIConfig(
        python_version=config_dict["PYTHON_VERSION"],
        uv_version=config_dict["UV_VERSION"],
        project_dir=config_dict["PROJECT_DIR"],
        test_results_file=config_dict["TEST_RESULTS_FILE"],
        security_report_file=config_dict["SECURITY_REPORT_FILE"],
        uv_index_url=config_dict["UV_INDEX_URL"],
        ruff_output_format=config_dict["RUFF_OUTPUT_FORMAT"],
        mypy_strict=config_dict["MYPY_STRICT"].lower() == "true",
        pytest_verbose=config_dict["PYTEST_VERBOSE"].lower() == "true",
        pytest_tb_style=config_dict["PYTEST_TB_STYLE"],
        log_level=args.log_level,
        config_file=args.config,
        skip_env_prep=args.skip_env_prep,
        skip_deps=args.skip_deps,
        skip_format=args.skip_format,
        skip_mypy=args.skip_mypy,
        skip_tests=args.skip_tests,
        skip_security=args.skip_security,
        upload_artifacts=args.upload_artifacts,
    )


def main() -> int:
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 创建配置
    config = create_config(args)

    # 创建CI实例并运行
    ci = CI(config)
    success = ci.run()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

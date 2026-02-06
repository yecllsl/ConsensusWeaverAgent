import asyncio
import sys
from typing import Optional

import click

from src.core.analyzer.consensus_analyzer import ConsensusAnalyzer
from src.core.executor.query_executor import QueryExecutor
from src.core.reporter.report_generator import ReportGenerator
from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.data.data_manager import DataManager
from src.infrastructure.llm.llm_service import LLMService
from src.infrastructure.logging.logger import get_logger
from src.infrastructure.tools.tool_manager import ToolManager
from src.service.interaction.interaction_engine import (
    InteractionEngine,
)
from src.service.strategy.execution_strategy import (
    ExecutionStrategyManager,
)
from src.ui.rich_console import RichConsole


@click.group()
@click.option("--config", "-c", default="config.yaml", help="配置文件路径")
@click.option("--verbose", "-v", is_flag=True, help="启用详细日志")
@click.pass_context
def cli(ctx: click.Context, config: str, verbose: bool) -> None:
    """智能问答协调终端应用"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["verbose"] = verbose
    ctx.obj["rich_console"] = RichConsole()

    if verbose:
        click.echo(f"使用配置文件: {config}")


@cli.command()
@click.option(
    "--i", "--iflow", "iflow_agent", is_flag=True, help="使用iflow作为主Agent"
)
@click.option("--q", "--qwen", "qwen_agent", is_flag=True, help="使用qwen作为主Agent")
@click.option(
    "--b",
    "--codebuddy",
    "codebuddy_agent",
    is_flag=True,
    help="使用codebuddy作为主Agent",
)
@click.pass_context
def run(
    ctx: click.Context,
    iflow_agent: bool,
    qwen_agent: bool,
    codebuddy_agent: bool,
) -> None:
    """运行交互式问答会话"""
    config = ctx.obj["config"]
    verbose = ctx.obj["verbose"]
    rich_console = ctx.obj["rich_console"]

    run_interactive_session(
        config, verbose, iflow_agent, qwen_agent, codebuddy_agent, rich_console
    )


@cli.command()
@click.argument("question")
@click.option(
    "--i", "--iflow", "iflow_agent", is_flag=True, help="使用iflow作为主Agent"
)
@click.option("--q", "--qwen", "qwen_agent", is_flag=True, help="使用qwen作为主Agent")
@click.option(
    "--b",
    "--codebuddy",
    "codebuddy_agent",
    is_flag=True,
    help="使用codebuddy作为主Agent",
)
@click.option("--output", "-o", help="输出文件路径")
@click.pass_context
def ask(
    ctx: click.Context,
    question: str,
    iflow_agent: bool,
    qwen_agent: bool,
    codebuddy_agent: bool,
    output: Optional[str],
) -> None:
    """直接询问单个问题"""
    config = ctx.obj["config"]
    verbose = ctx.obj["verbose"]
    rich_console = ctx.obj["rich_console"]

    run_single_question(
        config,
        verbose,
        question,
        iflow_agent,
        qwen_agent,
        codebuddy_agent,
        output,
        rich_console,
    )


@cli.command()
@click.pass_context
def check(ctx: click.Context) -> None:
    """检查系统环境和依赖"""
    rich_console = ctx.obj["rich_console"]

    rich_console.print_info("正在检查系统环境...")

    try:
        config_manager = ConfigManager(ctx.obj["config"])
        rich_console.print_info("✓ 配置文件加载成功")

        _llm_service = LLMService(config_manager)
        rich_console.print_info("✓ LLM服务初始化成功")

        _tool_manager = ToolManager(config_manager)
        rich_console.print_info("✓ 工具管理器初始化成功")

        _data_manager = DataManager()
        rich_console.print_info("✓ 数据管理器初始化成功")

        try:
            import trogon  # type: ignore
            rich_console.print_info("✓ Trogon可用")
        except ImportError:
            rich_console.print_warning("✗ Trogon不可用")

        rich_console.print_info("所有检查通过！")

    except Exception as e:
        rich_console.print_error(f"检查失败: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """显示版本信息"""
    rich_console = ctx.obj["rich_console"]
    rich_console.print_info("ConsensusWeaverAgent 版本: 0.4.0.dev0")


def run_interactive_session(
    config: str,
    verbose: bool,
    iflow_agent: bool,
    qwen_agent: bool,
    codebuddy_agent: bool,
    rich_console: RichConsole,
) -> None:
    """运行交互式会话"""
    # 检查参数互斥性
    agent_flags = [iflow_agent, qwen_agent, codebuddy_agent]
    if sum(agent_flags) > 1:
        rich_console.print_error("错误: 只能选择一个主Agent")
        sys.exit(1)

    # 确定主Agent类型
    main_agent = None
    if iflow_agent:
        main_agent = "iflow"
    elif qwen_agent:
        main_agent = "qwen"
    elif codebuddy_agent:
        main_agent = "codebuddy"

    # 初始化配置管理
    config_manager = ConfigManager(config)
    config_data = config_manager.get_config()

    # 初始化日志系统
    log_level = "debug" if verbose else config_data.app.log_level
    logger = get_logger(log_file=config_data.app.log_file, log_level=log_level)

    logger.info("启动智能问答协调终端应用")
    logger.info(f"使用配置文件: {config}")
    if main_agent:
        logger.info(f"使用外部工具作为主Agent: {main_agent}")
    else:
        logger.info("使用本地LLM作为主Agent")

    try:
        # 初始化数据管理器
        data_manager = DataManager()

        # 初始化LLM服务
        llm_service = LLMService(config_manager)

        # 初始化工具管理器
        tool_manager = ToolManager(config_manager)

        # 初始化交互引擎
        interaction_engine = InteractionEngine(
            llm_service,
            data_manager,
            config_data.app.max_clarification_rounds,
            main_agent,
        )

        # 初始化执行策略管理器
        execution_strategy_manager = ExecutionStrategyManager(
            llm_service, tool_manager, main_agent
        )

        # 初始化查询执行器
        query_executor = QueryExecutor(tool_manager, data_manager)

        # 初始化共识分析器
        consensus_analyzer = ConsensusAnalyzer(llm_service, data_manager)

        # 初始化报告生成器
        report_generator = ReportGenerator(data_manager)

        logger.info("所有组件初始化完成")

        # 开始用户交互
        asyncio.run(
            start_interaction(
                interaction_engine,
                execution_strategy_manager,
                query_executor,
                consensus_analyzer,
                report_generator,
                tool_manager,
                rich_console,
            )
        )

    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        rich_console.print_error(f"错误: {e}")
    finally:
        if "data_manager" in locals():
            data_manager.close()
        logger.info("关闭智能问答协调终端应用")


def run_single_question(
    config: str,
    verbose: bool,
    question: str,
    iflow_agent: bool,
    qwen_agent: bool,
    codebuddy_agent: bool,
    output: Optional[str],
    rich_console: RichConsole,
) -> None:
    """运行单个问题"""
    # 检查参数互斥性
    agent_flags = [iflow_agent, qwen_agent, codebuddy_agent]
    if sum(agent_flags) > 1:
        rich_console.print_error("错误: 只能选择一个主Agent")
        sys.exit(1)

    # 确定主Agent类型
    main_agent = None
    if iflow_agent:
        main_agent = "iflow"
    elif qwen_agent:
        main_agent = "qwen"
    elif codebuddy_agent:
        main_agent = "codebuddy"

    # 初始化配置管理
    config_manager = ConfigManager(config)
    config_data = config_manager.get_config()

    # 初始化日志系统
    log_level = "debug" if verbose else config_data.app.log_level
    logger = get_logger(log_file=config_data.app.log_file, log_level=log_level)

    logger.info(f"处理问题: {question}")

    try:
        # 初始化数据管理器
        data_manager = DataManager()

        # 初始化LLM服务
        llm_service = LLMService(config_manager)

        # 初始化工具管理器
        tool_manager = ToolManager(config_manager)

        # 初始化交互引擎
        interaction_engine = InteractionEngine(
            llm_service,
            data_manager,
            config_data.app.max_clarification_rounds,
            main_agent,
        )

        # 初始化执行策略管理器
        execution_strategy_manager = ExecutionStrategyManager(
            llm_service, tool_manager, main_agent
        )

        # 初始化查询执行器
        query_executor = QueryExecutor(tool_manager, data_manager)

        # 初始化共识分析器
        consensus_analyzer = ConsensusAnalyzer(llm_service, data_manager)

        # 初始化报告生成器
        report_generator = ReportGenerator(data_manager)

        # 开始交互会话
        state = interaction_engine.start_interaction(question)

        # 分析问题
        analysis = interaction_engine.analyze_question(state)

        # 重构问题
        refined_question = interaction_engine.refine_question(state)

        # 完成交互
        state = interaction_engine.complete_interaction(state)

        # 创建执行计划
        execution_plan = execution_strategy_manager.create_execution_plan(
            refined_question
        )

        if execution_plan.strategy == "direct_answer":
            # 直接回答简单问题
            rich_console.print_info("识别为简单问题，正在生成直接回答...")
            answer = interaction_engine.llm_service.answer_simple_question(
                refined_question
            )
            rich_console.print_info(f"直接回答：\n{answer}")
        else:
            # 复杂问题，执行并行查询
            rich_console.print_info("识别为复杂问题，正在调用外部工具进行并行查询...")
            rich_console.print_info(f"使用工具数量: {len(execution_plan.tools)}")
            rich_console.print_info(f"使用工具: {', '.join(execution_plan.tools)}")

            # 执行并行查询
            result = asyncio.run(
                query_executor.execute_queries(
                    state.session_id, refined_question, execution_plan.tools
                )
            )

            rich_console.print_info("查询完成：")
            rich_console.print_info(f"  - 成功: {result.success_count} 个")
            rich_console.print_info(f"  - 失败: {result.failure_count} 个")
            rich_console.print_info(f"  - 总耗时: {result.total_execution_time:.2f} 秒")

            # 分析共识度
            rich_console.print_info("正在分析共识度...")
            tool_results = query_executor.get_query_results(state.session_id)
            tool_results_dict = [
                {
                    "tool_name": result.tool_name,
                    "success": result.success,
                    "answer": result.answer,
                    "error_message": result.error_message,
                    "execution_time": result.execution_time,
                    "timestamp": result.timestamp,
                }
                for result in tool_results
            ]

            # 分析共识度
            consensus_analyzer.analyze_consensus(
                state.session_id, refined_question, tool_results_dict
            )

            # 生成报告
            rich_console.print_info("正在生成最终报告...")
            report = report_generator.generate_report(state.session_id)

            # 显示报告
            rich_console.print_report(str(report.content))

            # 保存报告
            if output:
                report_generator.save_report(report, output)
                rich_console.print_info(f"报告已保存到：{output}")

    except Exception as e:
        logger.error(f"处理问题时出错: {e}")
        rich_console.print_error(f"错误: {e}")
    finally:
        if "data_manager" in locals():
            data_manager.close()


async def start_interaction(
    interaction_engine: InteractionEngine,
    execution_strategy_manager: ExecutionStrategyManager,
    query_executor: QueryExecutor,
    consensus_analyzer: ConsensusAnalyzer,
    report_generator: ReportGenerator,
    tool_manager: ToolManager,
    rich_console: RichConsole,
) -> None:
    """开始与用户的交互"""
    logger = get_logger()

    # 欢迎信息
    rich_console.print_welcome()
    rich_console.print_info("欢迎使用智能问答协调终端！")
    rich_console.print_info("我可以帮您分析问题并获取多个AI工具的回答，最终生成综合报告。")
    rich_console.print_info("请输入您的问题，或输入 'quit' 退出应用。")

    while True:
        # 获取用户输入
        original_question = rich_console.input("\n请输入您的问题: ")

        if original_question.lower() == "quit":
            rich_console.print_info("感谢使用智能问答协调终端，再见！")
            break

        if not original_question.strip():
            rich_console.print_warning("问题不能为空，请重新输入。")
            continue

        try:
            # 开始交互会话
            state = interaction_engine.start_interaction(original_question)

            # 分析问题
            analysis = interaction_engine.analyze_question(state)

            # 澄清对话循环
            while (
                interaction_engine.is_clarification_needed(analysis)
                and state.clarification_rounds
                < interaction_engine.max_clarification_rounds
            ):
                # 生成澄清问题
                clarification_question = interaction_engine.generate_clarification(
                    state, analysis
                )
                if not clarification_question:
                    break

                # 获取用户澄清响应
                response = rich_console.input(
                    f"{clarification_question} (或输入 'skip' 跳过澄清): "
                )

                if response.lower() == "skip":
                    rich_console.print_info("跳过澄清步骤")
                    break

                # 处理澄清响应
                state = interaction_engine.handle_clarification_response(
                    state, response
                )

                # 重新分析问题
                analysis = interaction_engine.analyze_question(state)

            # 重构问题
            refined_question = interaction_engine.refine_question(state)

            # 确认重构后的问题
            confirm = rich_console.input(
                f"\n重构后的问题：{refined_question}\n是否继续？(y/n): "
            )
            if confirm.lower() != "y":
                rich_console.print_info("操作已取消")
                continue

            # 完成交互
            state = interaction_engine.complete_interaction(state)

            # 创建执行计划
            execution_plan = execution_strategy_manager.create_execution_plan(
                refined_question
            )

            if execution_plan.strategy == "direct_answer":
                # 直接回答简单问题
                rich_console.print_info("识别为简单问题，正在生成直接回答...")
                answer = interaction_engine.llm_service.answer_simple_question(
                    refined_question
                )
                rich_console.print_info(f"直接回答：\n{answer}")
            else:
                # 复杂问题，执行并行查询
                rich_console.print_info("识别为复杂问题，正在调用外部工具进行并行查询...")
                rich_console.print_info(f"使用工具数量: {len(execution_plan.tools)}")
                rich_console.print_info(f"使用工具: {', '.join(execution_plan.tools)}")

                # 检查网络连接
                if tool_manager.config.network.check_before_run:
                    has_internet = tool_manager.check_internet_connection()
                    if not has_internet:
                        rich_console.print_warning("警告：网络连接不可用，外部工具可能无法正常工作")
                        proceed = rich_console.input("是否继续？(y/n): ")
                        if proceed.lower() != "y":
                            rich_console.print_info("操作已取消")
                            continue

                # 执行并行查询
                result = await query_executor.execute_queries(
                    state.session_id, refined_question, execution_plan.tools
                )

                rich_console.print_info("查询完成：")
                rich_console.print_info(f"  - 成功: {result.success_count} 个")
                rich_console.print_info(f"  - 失败: {result.failure_count} 个")
                rich_console.print_info(
                    f"  - 总耗时: {result.total_execution_time:.2f} 秒"
                )

                # 分析共识度
                rich_console.print_info("正在分析共识度...")
                tool_results = query_executor.get_query_results(state.session_id)
                tool_results_dict = [
                    {
                        "tool_name": result.tool_name,
                        "success": result.success,
                        "answer": result.answer,
                        "error_message": result.error_message,
                        "execution_time": result.execution_time,
                        "timestamp": result.timestamp,
                    }
                    for result in tool_results
                ]

                # 分析共识度
                consensus_analyzer.analyze_consensus(
                    state.session_id, refined_question, tool_results_dict
                )

                # 生成报告
                rich_console.print_info("正在生成最终报告...")
                report = report_generator.generate_report(state.session_id)

                # 显示报告
                rich_console.print_report(str(report.content))

                # 保存报告
                save_report = rich_console.input("\n是否保存报告？(y/n): ")
                if save_report.lower() == "y":
                    file_path = report_generator.save_report(report)
                    rich_console.print_info(f"报告已保存到：{file_path}")

        except Exception as e:
            logger.error(f"处理问题时出错: {e}")
            rich_console.print_error(f"错误: {e}")
            rich_console.print_info("请重试或输入 'quit' 退出应用。")


def main() -> None:
    """主函数"""
    try:
        import trogon  # type: ignore
        cli_with_tui = trogon.tui()(cli)
        cli_with_tui()
    except ImportError:
        cli()


if __name__ == "__main__":
    main()

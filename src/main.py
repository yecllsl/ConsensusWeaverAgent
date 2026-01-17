import asyncio
import sys

import click

# 添加项目根目录到Python路径
sys.path.append('.')

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


@click.command()
@click.option('--config', '-c', default='config.yaml', help='配置文件路径')
@click.option('--verbose', '-v', is_flag=True, help='启用详细日志')
def main(config: str, verbose: bool):
    """智能问答协调终端应用"""
    # 初始化配置管理
    config_manager = ConfigManager(config)
    config_data = config_manager.get_config()
    
    # 初始化日志系统
    log_level = 'debug' if verbose else config_data.app.log_level
    logger = get_logger(log_file=config_data.app.log_file, log_level=log_level)
    
    logger.info("启动智能问答协调终端应用")
    logger.info(f"使用配置文件: {config}")
    
    try:
        # 初始化数据管理器
        data_manager = DataManager()
        
        # 初始化LLM服务
        llm_service = LLMService(config_manager)
        
        # 初始化工具管理器
        tool_manager = ToolManager(config_manager)
        
        # 初始化交互引擎
        interaction_engine = InteractionEngine(llm_service, data_manager, config_data.app.max_clarification_rounds)
        
        # 初始化执行策略管理器
        execution_strategy_manager = ExecutionStrategyManager(llm_service, tool_manager)
        
        # 初始化查询执行器
        query_executor = QueryExecutor(tool_manager, data_manager)
        
        # 初始化共识分析器
        consensus_analyzer = ConsensusAnalyzer(llm_service, data_manager)
        
        # 初始化报告生成器
        report_generator = ReportGenerator(data_manager)
        
        logger.info("所有组件初始化完成")
        
        # 开始用户交互
        asyncio.run(start_interaction(
            interaction_engine,
            execution_strategy_manager,
            query_executor,
            consensus_analyzer,
            report_generator,
            tool_manager
        ))
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        click.echo(f"错误: {e}", err=True)
    finally:
        if 'data_manager' in locals():
            data_manager.close()
        logger.info("关闭智能问答协调终端应用")

async def start_interaction(
    interaction_engine: InteractionEngine,
    execution_strategy_manager: ExecutionStrategyManager,
    query_executor: QueryExecutor,
    consensus_analyzer: ConsensusAnalyzer,
    report_generator: ReportGenerator,
    tool_manager: ToolManager
):
    """开始与用户的交互"""
    logger = get_logger()
    
    # 欢迎信息
    click.echo("=" * 60)
    click.echo("智能问答协调终端")
    click.echo("=" * 60)
    click.echo("欢迎使用智能问答协调终端！")
    click.echo("我可以帮您分析问题并获取多个AI工具的回答，最终生成综合报告。")
    click.echo("请输入您的问题，或输入 'quit' 退出应用。")
    click.echo("=" * 60)
    
    while True:
        # 获取用户输入
        original_question = click.prompt("\n请输入您的问题")
        
        if original_question.lower() == 'quit':
            click.echo("感谢使用智能问答协调终端，再见！")
            break
        
        if not original_question.strip():
            click.echo("问题不能为空，请重新输入。")
            continue
        
        try:
            # 开始交互会话
            state = interaction_engine.start_interaction(original_question)
            
            # 分析问题
            analysis = interaction_engine.analyze_question(state)
            
            # 澄清对话循环
            while interaction_engine.is_clarification_needed(analysis) and state.clarification_rounds < interaction_engine.max_clarification_rounds:
                # 生成澄清问题
                clarification_question = interaction_engine.generate_clarification(state, analysis)
                if not clarification_question:
                    break
                
                # 获取用户澄清响应
                response = click.prompt(f"{clarification_question} (或输入 'skip' 跳过澄清)")
                
                if response.lower() == 'skip':
                    click.echo("跳过澄清步骤")
                    break
                
                # 处理澄清响应
                state = interaction_engine.handle_clarification_response(state, response)
                
                # 重新分析问题
                analysis = interaction_engine.analyze_question(state)
            
            # 重构问题
            refined_question = interaction_engine.refine_question(state)
            
            # 确认重构后的问题
            confirm = click.confirm(f"\n重构后的问题：{refined_question}\n是否继续？")
            if not confirm:
                click.echo("操作已取消")
                continue
            
            # 完成交互
            state = interaction_engine.complete_interaction(state)
            
            # 创建执行计划
            execution_plan = execution_strategy_manager.create_execution_plan(refined_question)
            
            if execution_plan.strategy == "direct_answer":
                # 直接回答简单问题
                click.echo("\n识别为简单问题，正在生成直接回答...")
                answer = interaction_engine.llm_service.answer_simple_question(refined_question)
                click.echo(f"\n直接回答：\n{answer}")
            else:
                # 复杂问题，执行并行查询
                click.echo(f"\n识别为复杂问题，正在调用 {len(execution_plan.tools)} 个外部工具进行并行查询...")
                click.echo(f"使用工具: {', '.join(execution_plan.tools)}")
                
                # 检查网络连接
                if tool_manager.config.network.check_before_run:
                    has_internet = tool_manager.check_internet_connection()
                    if not has_internet:
                        click.echo("警告：网络连接不可用，外部工具可能无法正常工作")
                        proceed = click.confirm("是否继续？")
                        if not proceed:
                            click.echo("操作已取消")
                            continue
                
                # 执行并行查询
                result = await query_executor.execute_queries(
                    state.session_id,
                    refined_question,
                    execution_plan.tools
                )
                
                click.echo(f"\n查询完成：成功 {result.success_count} 个，失败 {result.failure_count} 个，总耗时 {result.total_execution_time:.2f} 秒")
                
                # 分析共识度
                click.echo("\n正在分析共识度...")
                tool_results = query_executor.get_query_results(state.session_id)
                tool_results_dict = [
                    {
                        "tool_name": result.tool_name,
                        "success": result.success,
                        "answer": result.answer,
                        "error_message": result.error_message,
                        "execution_time": result.execution_time,
                        "timestamp": result.timestamp
                    }
                    for result in tool_results
                ]
                
                consensus_result = consensus_analyzer.analyze_consensus(
                    state.session_id,
                    refined_question,
                    tool_results_dict
                )
                
                # 生成报告
                click.echo("\n正在生成最终报告...")
                report = report_generator.generate_report(state.session_id)
                
                # 显示报告
                click.echo("\n" + "=" * 60)
                click.echo("最终报告")
                click.echo("=" * 60)
                click.echo(report.content)
                
                # 保存报告
                save_report = click.confirm("\n是否保存报告？")
                if save_report:
                    file_path = report_generator.save_report(report)
                    click.echo(f"报告已保存到：{file_path}")
                    
        except Exception as e:
            logger.error(f"处理问题时出错: {e}")
            click.echo(f"错误: {e}", err=True)
            click.echo("请重试或输入 'quit' 退出应用。")

if __name__ == "__main__":
    main()

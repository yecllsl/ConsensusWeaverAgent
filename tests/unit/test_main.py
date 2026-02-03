"""测试主模块"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner


class TestMainFunction:
    """测试主函数"""

    def test_main_with_invalid_agent_flags(self):
        """测试使用多个Agent标志时的错误处理"""
        from src.main import main

        runner = CliRunner()
        result = runner.invoke(main, ["--config", "config.yaml", "--iflow", "--qwen"])

        assert result.exit_code == 1
        assert "只能选择一个主Agent" in result.output

    @patch("src.main.ConfigManager")
    @patch("src.main.get_logger")
    @patch("src.main.DataManager")
    @patch("src.main.LLMService")
    @patch("src.main.ToolManager")
    @patch("src.main.InteractionEngine")
    @patch("src.main.ExecutionStrategyManager")
    @patch("src.main.QueryExecutor")
    @patch("src.main.ConsensusAnalyzer")
    @patch("src.main.ReportGenerator")
    @patch("src.main.asyncio.run")
    def test_main_initialization_success(
        self,
        mock_asyncio_run,
        mock_report_generator,
        mock_consensus_analyzer,
        mock_query_executor,
        mock_execution_strategy_manager,
        mock_interaction_engine,
        mock_tool_manager,
        mock_llm_service,
        mock_data_manager,
        mock_get_logger,
        mock_config_manager,
    ):
        """测试主函数成功初始化"""
        from src.main import main

        mock_config = MagicMock()
        mock_config.app.log_level = "info"
        mock_config.app.log_file = "app.log"
        mock_config_manager.return_value.get_config.return_value = mock_config

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_data_manager_instance = MagicMock()
        mock_data_manager.return_value = mock_data_manager_instance

        mock_llm_service_instance = MagicMock()
        mock_llm_service.return_value = mock_llm_service_instance

        mock_tool_manager_instance = MagicMock()
        mock_tool_manager.return_value = mock_tool_manager_instance

        mock_interaction_engine_instance = MagicMock()
        mock_interaction_engine.return_value = mock_interaction_engine_instance

        mock_execution_strategy_manager_instance = MagicMock()
        mock_execution_strategy_manager.return_value = (
            mock_execution_strategy_manager_instance
        )

        mock_query_executor_instance = MagicMock()
        mock_query_executor.return_value = mock_query_executor_instance

        mock_consensus_analyzer_instance = MagicMock()
        mock_consensus_analyzer.return_value = mock_consensus_analyzer_instance

        mock_report_generator_instance = MagicMock()
        mock_report_generator.return_value = mock_report_generator_instance

        runner = CliRunner()
        runner.invoke(main, ["--config", "config.yaml"])

        mock_config_manager.assert_called_once_with("config.yaml")
        mock_get_logger.assert_called_once_with(log_file="app.log", log_level="info")


class TestStartInteraction:
    """测试交互启动函数"""

    @pytest.fixture
    def mock_components(self):
        """创建模拟组件"""
        return {
            "interaction_engine": MagicMock(),
            "execution_strategy_manager": MagicMock(),
            "query_executor": MagicMock(),
            "consensus_analyzer": MagicMock(),
            "report_generator": MagicMock(),
            "tool_manager": MagicMock(),
        }

    @patch("src.main.click")
    @pytest.mark.asyncio
    async def test_start_interaction_quit_command(self, mock_click, mock_components):
        """测试退出命令"""
        from src.main import start_interaction

        mock_click.prompt.side_effect = ["quit"]

        await start_interaction(**mock_components)

        mock_click.echo.assert_called()

    @patch("src.main.click")
    @pytest.mark.asyncio
    async def test_start_interaction_empty_question(self, mock_click, mock_components):
        """测试空问题处理"""
        from src.main import start_interaction

        mock_click.prompt.side_effect = ["   ", "quit"]

        await start_interaction(**mock_components)

        mock_click.echo.assert_called()

    @patch("src.main.click")
    @pytest.mark.asyncio
    async def test_start_interaction_simple_question(self, mock_click, mock_components):
        """测试简单问题处理"""
        from src.main import start_interaction

        mock_click.prompt.side_effect = ["什么是Python？", "quit"]
        mock_click.confirm.return_value = True

        mock_components[
            "interaction_engine"
        ].start_interaction.return_value = MagicMock()
        mock_components[
            "interaction_engine"
        ].analyze_question.return_value = MagicMock()
        mock_components[
            "interaction_engine"
        ].is_clarification_needed.return_value = False
        mock_components[
            "interaction_engine"
        ].refine_question.return_value = "什么是Python？"
        mock_components[
            "interaction_engine"
        ].complete_interaction.return_value = MagicMock()

        mock_components[
            "execution_strategy_manager"
        ].create_execution_plan.return_value = MagicMock(strategy="direct_answer")

        mock_components[
            "interaction_engine"
        ].llm_service.answer_simple_question.return_value = "Python是一种编程语言"

        await start_interaction(**mock_components)

        mock_click.echo.assert_called()

    @patch("src.main.click")
    @pytest.mark.asyncio
    async def test_start_interaction_complex_question(
        self, mock_click, mock_components
    ):
        """测试复杂问题处理"""
        from src.main import start_interaction

        mock_click.prompt.side_effect = ["比较Python和Java的优缺点", "quit"]
        mock_click.confirm.return_value = False

        mock_components[
            "interaction_engine"
        ].start_interaction.return_value = MagicMock()
        mock_components[
            "interaction_engine"
        ].analyze_question.return_value = MagicMock()
        mock_components[
            "interaction_engine"
        ].is_clarification_needed.return_value = False
        mock_components[
            "interaction_engine"
        ].refine_question.return_value = "比较Python和Java的优缺点"
        mock_components[
            "interaction_engine"
        ].complete_interaction.return_value = MagicMock()

        mock_components[
            "execution_strategy_manager"
        ].create_execution_plan.return_value = MagicMock(
            strategy="parallel_query", tools=["iflow", "qwen"]
        )

        mock_components["query_executor"].execute_queries = AsyncMock(
            return_value=MagicMock(
                success_count=2, failure_count=0, total_execution_time=10.0
            )
        )
        mock_components["query_executor"].get_query_results.return_value = []

        await start_interaction(**mock_components)

    @patch("src.main.click")
    @pytest.mark.asyncio
    async def test_start_interaction_with_clarification(
        self, mock_click, mock_components
    ):
        """测试澄清流程"""
        from src.main import start_interaction

        mock_click.prompt.side_effect = ["如何使用Python？", "skip", "quit"]
        mock_click.confirm.return_value = True

        mock_components[
            "interaction_engine"
        ].start_interaction.return_value = MagicMock()
        mock_components[
            "interaction_engine"
        ].analyze_question.return_value = MagicMock()
        mock_components[
            "interaction_engine"
        ].is_clarification_needed.return_value = True
        mock_components[
            "interaction_engine"
        ].generate_clarification.return_value = "您想了解Python的哪个方面？"
        mock_components[
            "interaction_engine"
        ].handle_clarification_response.return_value = MagicMock()
        mock_components[
            "interaction_engine"
        ].refine_question.return_value = "如何使用Python进行Web开发？"
        mock_components[
            "interaction_engine"
        ].complete_interaction.return_value = MagicMock()
        mock_components["interaction_engine"].max_clarification_rounds = 3

        mock_components[
            "execution_strategy_manager"
        ].create_execution_plan.return_value = MagicMock(strategy="direct_answer")

        mock_components[
            "interaction_engine"
        ].llm_service.answer_simple_question.return_value = "Python可以用于Web开发"

        await start_interaction(**mock_components)

    @patch("src.main.click")
    @pytest.mark.asyncio
    async def test_start_interaction_exception_handling(
        self, mock_click, mock_components
    ):
        """测试异常处理"""
        from src.main import start_interaction

        mock_click.prompt.side_effect = ["测试问题", "quit"]
        mock_click.echo = MagicMock()

        mock_components["interaction_engine"].start_interaction.side_effect = Exception(
            "处理失败"
        )

        await start_interaction(**mock_components)

        mock_click.echo.assert_called()


class TestAgentSelection:
    """测试Agent选择逻辑"""

    def test_main_with_iflow_agent(self):
        """测试选择iflow作为主Agent"""
        from src.main import main

        with (
            patch("src.main.ConfigManager") as mock_config_manager,
            patch("src.main.get_logger") as mock_get_logger,
            patch("src.main.DataManager") as mock_data_manager,
            patch("src.main.LLMService") as mock_llm_service,
            patch("src.main.ToolManager") as mock_tool_manager,
            patch("src.main.InteractionEngine") as mock_interaction_engine,
            patch(
                "src.main.ExecutionStrategyManager"
            ) as mock_execution_strategy_manager,
            patch("src.main.QueryExecutor") as mock_query_executor,
            patch("src.main.ConsensusAnalyzer") as mock_consensus_analyzer,
            patch("src.main.ReportGenerator") as mock_report_generator,
            patch("src.main.asyncio.run"),
        ):
            mock_config = MagicMock()
            mock_config.app.log_level = "info"
            mock_config.app.log_file = "app.log"
            mock_config_manager.return_value.get_config.return_value = mock_config

            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            mock_data_manager.return_value = MagicMock()
            mock_llm_service.return_value = MagicMock()
            mock_tool_manager.return_value = MagicMock()
            mock_interaction_engine.return_value = MagicMock()
            mock_execution_strategy_manager.return_value = MagicMock()
            mock_query_executor.return_value = MagicMock()
            mock_consensus_analyzer.return_value = MagicMock()
            mock_report_generator.return_value = MagicMock()

            runner = CliRunner()
            runner.invoke(main, ["--config", "config.yaml", "--iflow"])

            mock_interaction_engine.assert_called_once()

    def test_main_with_qwen_agent(self):
        """测试选择qwen作为主Agent"""
        from src.main import main

        with (
            patch("src.main.ConfigManager") as mock_config_manager,
            patch("src.main.get_logger") as mock_get_logger,
            patch("src.main.DataManager") as mock_data_manager,
            patch("src.main.LLMService") as mock_llm_service,
            patch("src.main.ToolManager") as mock_tool_manager,
            patch("src.main.InteractionEngine") as mock_interaction_engine,
            patch(
                "src.main.ExecutionStrategyManager"
            ) as mock_execution_strategy_manager,
            patch("src.main.QueryExecutor") as mock_query_executor,
            patch("src.main.ConsensusAnalyzer") as mock_consensus_analyzer,
            patch("src.main.ReportGenerator") as mock_report_generator,
            patch("src.main.asyncio.run"),
        ):
            mock_config = MagicMock()
            mock_config.app.log_level = "info"
            mock_config.app.log_file = "app.log"
            mock_config_manager.return_value.get_config.return_value = mock_config

            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            mock_data_manager.return_value = MagicMock()
            mock_llm_service.return_value = MagicMock()
            mock_tool_manager.return_value = MagicMock()
            mock_interaction_engine.return_value = MagicMock()
            mock_execution_strategy_manager.return_value = MagicMock()
            mock_query_executor.return_value = MagicMock()
            mock_consensus_analyzer.return_value = MagicMock()
            mock_report_generator.return_value = MagicMock()

            runner = CliRunner()
            runner.invoke(main, ["--config", "config.yaml", "--qwen"])

            mock_interaction_engine.assert_called_once()

    def test_main_with_codebuddy_agent(self):
        """测试选择codebuddy作为主Agent"""
        from src.main import main

        with (
            patch("src.main.ConfigManager") as mock_config_manager,
            patch("src.main.get_logger") as mock_get_logger,
            patch("src.main.DataManager") as mock_data_manager,
            patch("src.main.LLMService") as mock_llm_service,
            patch("src.main.ToolManager") as mock_tool_manager,
            patch("src.main.InteractionEngine") as mock_interaction_engine,
            patch(
                "src.main.ExecutionStrategyManager"
            ) as mock_execution_strategy_manager,
            patch("src.main.QueryExecutor") as mock_query_executor,
            patch("src.main.ConsensusAnalyzer") as mock_consensus_analyzer,
            patch("src.main.ReportGenerator") as mock_report_generator,
            patch("src.main.asyncio.run"),
        ):
            mock_config = MagicMock()
            mock_config.app.log_level = "info"
            mock_config.app.log_file = "app.log"
            mock_config_manager.return_value.get_config.return_value = mock_config

            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            mock_data_manager.return_value = MagicMock()
            mock_llm_service.return_value = MagicMock()
            mock_tool_manager.return_value = MagicMock()
            mock_interaction_engine.return_value = MagicMock()
            mock_execution_strategy_manager.return_value = MagicMock()
            mock_query_executor.return_value = MagicMock()
            mock_consensus_analyzer.return_value = MagicMock()
            mock_report_generator.return_value = MagicMock()

            runner = CliRunner()
            runner.invoke(main, ["--config", "config.yaml", "--codebuddy"])

            mock_interaction_engine.assert_called_once()


class TestNetworkCheck:
    """测试网络检查逻辑"""

    @pytest.mark.asyncio
    async def test_network_check_before_run(self):
        """测试网络检查功能"""
        from src.main import start_interaction

        mock_components = {
            "interaction_engine": MagicMock(),
            "execution_strategy_manager": MagicMock(),
            "query_executor": MagicMock(),
            "consensus_analyzer": MagicMock(),
            "report_generator": MagicMock(),
            "tool_manager": MagicMock(),
        }

        with patch("src.main.click") as mock_click:
            mock_click.prompt.side_effect = ["测试问题", "quit"]
            mock_click.confirm.return_value = False

            mock_components[
                "interaction_engine"
            ].start_interaction.return_value = MagicMock()
            mock_components[
                "interaction_engine"
            ].analyze_question.return_value = MagicMock()
            mock_components[
                "interaction_engine"
            ].is_clarification_needed.return_value = False
            mock_components[
                "interaction_engine"
            ].refine_question.return_value = "测试问题"
            mock_components[
                "interaction_engine"
            ].complete_interaction.return_value = MagicMock()

            mock_components[
                "execution_strategy_manager"
            ].create_execution_plan.return_value = MagicMock(
                strategy="parallel_query", tools=["iflow"]
            )

            mock_components["tool_manager"].config.network.check_before_run = True
            mock_components[
                "tool_manager"
            ].check_internet_connection.return_value = False

            await start_interaction(**mock_components)


class TestReportGeneration:
    """测试报告生成逻辑"""

    @pytest.mark.asyncio
    async def test_report_generation_and_save(self):
        """测试报告生成和保存"""
        from src.main import start_interaction

        mock_components = {
            "interaction_engine": MagicMock(),
            "execution_strategy_manager": MagicMock(),
            "query_executor": MagicMock(),
            "consensus_analyzer": MagicMock(),
            "report_generator": MagicMock(),
            "tool_manager": MagicMock(),
        }

        with patch("src.main.click") as mock_click:
            mock_click.prompt.side_effect = ["生成报告的问题", "quit"]
            mock_click.confirm.return_value = True

            mock_components[
                "interaction_engine"
            ].start_interaction.return_value = MagicMock()
            mock_components[
                "interaction_engine"
            ].analyze_question.return_value = MagicMock()
            mock_components[
                "interaction_engine"
            ].is_clarification_needed.return_value = False
            mock_components[
                "interaction_engine"
            ].refine_question.return_value = "生成报告的问题"
            mock_components[
                "interaction_engine"
            ].complete_interaction.return_value = MagicMock()

            mock_components[
                "execution_strategy_manager"
            ].create_execution_plan.return_value = MagicMock(
                strategy="parallel_query", tools=["iflow", "qwen"]
            )

            mock_components["query_executor"].execute_queries = AsyncMock(
                return_value=MagicMock(
                    success_count=2, failure_count=0, total_execution_time=10.0
                )
            )
            mock_components["query_executor"].get_query_results.return_value = []

            mock_components["consensus_analyzer"].analyze_consensus.return_value = None

            mock_report = MagicMock(content="测试报告内容")
            mock_components[
                "report_generator"
            ].generate_report.return_value = mock_report
            mock_components["report_generator"].save_report.return_value = "report.txt"

            await start_interaction(**mock_components)

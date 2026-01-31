from unittest.mock import Mock, patch

import pytest

from src.service.strategy.execution_strategy import (
    ExecutionPlan,
    ExecutionStrategyManager,
)


@pytest.fixture
def mock_llm_service():
    llm_service = Mock()
    llm_service.classify_question_complexity = Mock(return_value="simple")
    llm_service.answer_simple_question = Mock(return_value="简单回答")
    return llm_service


@pytest.fixture
def mock_tool_manager():
    tool_manager = Mock()

    tool1 = Mock()
    tool1.name = "tool1"
    tool2 = Mock()
    tool2.name = "tool2"

    tool_manager.enabled_tools = [tool1, tool2]
    tool_manager.config = Mock()
    tool_manager.config.network = Mock()
    tool_manager.config.network.check_before_run = False
    tool_manager.check_internet_connection = Mock(return_value=True)
    return tool_manager


@pytest.fixture
def execution_strategy_manager(mock_llm_service, mock_tool_manager):
    return ExecutionStrategyManager(mock_llm_service, mock_tool_manager)


def test_execution_strategy_manager_initialization(
    execution_strategy_manager, mock_llm_service, mock_tool_manager
):
    assert execution_strategy_manager.llm_service == mock_llm_service
    assert execution_strategy_manager.tool_manager == mock_tool_manager
    assert execution_strategy_manager.external_agent is None


def test_create_execution_plan_simple(execution_strategy_manager, mock_llm_service):
    question = "简单问题"

    mock_llm_service.classify_question_complexity.return_value = "simple"

    plan = execution_strategy_manager.create_execution_plan(question)

    assert plan.strategy == "direct_answer"
    assert plan.question == question
    assert plan.tools == []


def test_create_execution_plan_complex(execution_strategy_manager, mock_llm_service):
    question = "复杂问题"

    mock_llm_service.classify_question_complexity.return_value = "complex"

    plan = execution_strategy_manager.create_execution_plan(question)

    assert plan.strategy == "parallel_query"
    assert plan.question == question
    assert len(plan.tools) == 2


def test_create_execution_plan_exception(execution_strategy_manager, mock_llm_service):
    question = "测试问题"

    mock_llm_service.classify_question_complexity.side_effect = Exception("测试异常")

    with pytest.raises(Exception):
        execution_strategy_manager.create_execution_plan(question)


def test_select_tools(execution_strategy_manager):
    question = "测试问题"

    tools = execution_strategy_manager._select_tools(question)

    assert len(tools) == 2
    assert "tool1" in tools
    assert "tool2" in tools


def test_select_tools_exception(execution_strategy_manager, mock_tool_manager):
    mock_tool_manager.enabled_tools = None

    with pytest.raises(Exception):
        execution_strategy_manager._select_tools("测试问题")


def test_execute_plan_direct_answer(execution_strategy_manager, mock_llm_service):
    plan = ExecutionPlan(strategy="direct_answer", question="简单问题")

    mock_llm_service.answer_simple_question.return_value = "简单回答"

    result = execution_strategy_manager.execute_plan(plan)

    assert result["strategy"] == "direct_answer"
    assert result["success"] is True
    assert result["answer"] == "简单回答"
    assert result["tools"] == []


def test_execute_plan_parallel_query(execution_strategy_manager):
    plan = ExecutionPlan(
        strategy="parallel_query", question="复杂问题", tools=["tool1", "tool2"]
    )

    result = execution_strategy_manager.execute_plan(plan)

    assert result["strategy"] == "parallel_query"
    assert result["success"] is True
    assert result["question"] == "复杂问题"
    assert result["tools"] == ["tool1", "tool2"]


def test_execute_plan_exception(execution_strategy_manager, mock_llm_service):
    plan = ExecutionPlan(strategy="direct_answer", question="简单问题")

    mock_llm_service.answer_simple_question.side_effect = Exception("测试异常")

    with pytest.raises(Exception):
        execution_strategy_manager.execute_plan(plan)


def test_validate_plan_direct_answer(execution_strategy_manager):
    plan = ExecutionPlan(strategy="direct_answer", question="简单问题")

    is_valid = execution_strategy_manager.validate_plan(plan)

    assert is_valid is True


def test_validate_plan_parallel_query_valid(execution_strategy_manager):
    plan = ExecutionPlan(
        strategy="parallel_query", question="复杂问题", tools=["tool1", "tool2"]
    )

    is_valid = execution_strategy_manager.validate_plan(plan)

    assert is_valid is True


def test_validate_plan_parallel_query_no_tools(execution_strategy_manager):
    plan = ExecutionPlan(strategy="parallel_query", question="复杂问题", tools=[])

    is_valid = execution_strategy_manager.validate_plan(plan)

    assert is_valid is False


def test_validate_plan_parallel_query_invalid_tool(execution_strategy_manager):
    plan = ExecutionPlan(
        strategy="parallel_query", question="复杂问题", tools=["invalid_tool"]
    )

    is_valid = execution_strategy_manager.validate_plan(plan)

    assert is_valid is False


def test_validate_plan_parallel_query_no_internet(
    execution_strategy_manager, mock_tool_manager
):
    plan = ExecutionPlan(
        strategy="parallel_query", question="复杂问题", tools=["tool1", "tool2"]
    )

    mock_tool_manager.config.network.check_before_run = True
    mock_tool_manager.check_internet_connection.return_value = False

    is_valid = execution_strategy_manager.validate_plan(plan)

    assert is_valid is False


def test_validate_plan_exception(execution_strategy_manager, mock_tool_manager):
    plan = ExecutionPlan(
        strategy="parallel_query", question="复杂问题", tools=["tool1", "tool2"]
    )

    mock_tool_manager.enabled_tools = None

    with pytest.raises(Exception):
        execution_strategy_manager.validate_plan(plan)


def test_adjust_plan_direct_answer_success(execution_strategy_manager):
    plan = ExecutionPlan(strategy="direct_answer", question="简单问题")
    feedback = {"success": True}

    adjusted_plan = execution_strategy_manager.adjust_plan(plan, feedback)

    assert adjusted_plan.strategy == "direct_answer"


def test_adjust_plan_direct_answer_failure(execution_strategy_manager):
    plan = ExecutionPlan(strategy="direct_answer", question="简单问题")
    feedback = {"success": False}

    adjusted_plan = execution_strategy_manager.adjust_plan(plan, feedback)

    assert adjusted_plan.strategy == "parallel_query"
    assert len(adjusted_plan.tools) == 2


def test_adjust_plan_parallel_query_failure_reduce_tools(execution_strategy_manager):
    plan = ExecutionPlan(
        strategy="parallel_query", question="复杂问题", tools=["tool1", "tool2"]
    )
    feedback = {"success": False}

    adjusted_plan = execution_strategy_manager.adjust_plan(plan, feedback)

    assert adjusted_plan.strategy == "parallel_query"
    assert len(adjusted_plan.tools) == 1


def test_adjust_plan_parallel_query_failure_switch_strategy(execution_strategy_manager):
    plan = ExecutionPlan(
        strategy="parallel_query", question="复杂问题", tools=["tool1"]
    )
    feedback = {"success": False}

    adjusted_plan = execution_strategy_manager.adjust_plan(plan, feedback)

    assert adjusted_plan.strategy == "direct_answer"


def test_adjust_plan_exception(execution_strategy_manager):
    plan = ExecutionPlan(strategy="direct_answer", question="简单问题")
    feedback = {"success": False}

    execution_strategy_manager._select_tools = Mock(side_effect=Exception("测试异常"))

    with pytest.raises(Exception):
        execution_strategy_manager.adjust_plan(plan, feedback)


def test_execution_plan_creation():
    plan = ExecutionPlan(strategy="direct_answer", question="测试问题")

    assert plan.strategy == "direct_answer"
    assert plan.question == "测试问题"
    assert plan.tools == []


def test_execution_plan_creation_with_tools():
    plan = ExecutionPlan(
        strategy="parallel_query", question="测试问题", tools=["tool1", "tool2"]
    )

    assert plan.strategy == "parallel_query"
    assert plan.question == "测试问题"
    assert len(plan.tools) == 2


def test_execution_strategy_manager_with_external_agent(
    mock_llm_service, mock_tool_manager
):
    mock_external_agent = Mock()
    mock_external_agent.classify_question_complexity = Mock(return_value="simple")

    with patch(
        "src.service.strategy.execution_strategy.create_external_agent"
    ) as mock_create:
        mock_create.return_value = mock_external_agent

        manager = ExecutionStrategyManager(
            llm_service=mock_llm_service,
            tool_manager=mock_tool_manager,
            main_agent="test_agent",
        )

        assert manager.external_agent is not None

        plan = manager.create_execution_plan("测试问题")

        assert plan.strategy == "direct_answer"
        assert mock_external_agent.classify_question_complexity.called


def test_execute_plan_with_external_agent(mock_llm_service, mock_tool_manager):
    mock_external_agent = Mock()
    mock_external_agent.answer_simple_question = Mock(return_value="外部Agent回答")

    with patch(
        "src.service.strategy.execution_strategy.create_external_agent"
    ) as mock_create:
        mock_create.return_value = mock_external_agent

        manager = ExecutionStrategyManager(
            llm_service=mock_llm_service,
            tool_manager=mock_tool_manager,
            main_agent="test_agent",
        )

        plan = ExecutionPlan(strategy="direct_answer", question="简单问题")
        result = manager.execute_plan(plan)

        assert result["answer"] == "外部Agent回答"
        assert mock_external_agent.answer_simple_question.called

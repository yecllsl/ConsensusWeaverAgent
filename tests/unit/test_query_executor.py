from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.core.executor.query_executor import QueryExecutor
from src.infrastructure.tools.tool_manager import ToolResult


@pytest.fixture
def mock_tool_manager():
    tool_manager = Mock()

    tool1 = Mock()
    tool1.name = "tool1"
    tool2 = Mock()
    tool2.name = "tool2"

    tool_manager.enabled_tools = [tool1, tool2]
    tool_manager.run_multiple_tools = AsyncMock()
    tool_manager.run_tool = AsyncMock()
    return tool_manager


@pytest.fixture
def mock_data_manager():
    data_manager = Mock()
    data_manager.save_tool_result = Mock()
    data_manager.get_tool_results = Mock(return_value=[])
    return data_manager


@pytest.fixture
def query_executor(mock_tool_manager, mock_data_manager):
    return QueryExecutor(mock_tool_manager, mock_data_manager)


@pytest.mark.asyncio
async def test_execute_queries_success(
    query_executor, mock_tool_manager, mock_data_manager
):
    session_id = 1
    question = "测试问题"
    tools = ["tool1", "tool2"]

    mock_tool_manager.run_multiple_tools.return_value = [
        ToolResult(
            tool_name="tool1",
            success=True,
            answer="答案1",
            error_message=None,
            execution_time=1.0,
            timestamp=datetime.now().isoformat(),
        ),
        ToolResult(
            tool_name="tool2",
            success=True,
            answer="答案2",
            error_message=None,
            execution_time=1.0,
            timestamp=datetime.now().isoformat(),
        ),
    ]

    result = await query_executor.execute_queries(session_id, question, tools)

    assert result.session_id == session_id
    assert result.question == question
    assert result.success_count == 2
    assert result.failure_count == 0
    assert result.completed is True
    assert len(result.tool_results) == 2
    assert mock_data_manager.save_tool_result.call_count == 2


@pytest.mark.asyncio
async def test_execute_queries_partial_failure(
    query_executor, mock_tool_manager, mock_data_manager
):
    session_id = 1
    question = "测试问题"
    tools = ["tool1", "tool2"]

    mock_tool_manager.run_multiple_tools.return_value = [
        ToolResult(
            tool_name="tool1",
            success=True,
            answer="答案1",
            error_message=None,
            execution_time=1.0,
            timestamp=datetime.now().isoformat(),
        ),
        ToolResult(
            tool_name="tool2",
            success=False,
            answer=None,
            error_message="错误",
            execution_time=1.0,
            timestamp=datetime.now().isoformat(),
        ),
    ]

    result = await query_executor.execute_queries(session_id, question, tools)

    assert result.success_count == 1
    assert result.failure_count == 1


@pytest.mark.asyncio
async def test_execute_queries_exception(query_executor, mock_tool_manager):
    session_id = 1
    question = "测试问题"
    tools = ["tool1"]

    mock_tool_manager.run_multiple_tools.side_effect = Exception("测试异常")

    with pytest.raises(Exception):
        await query_executor.execute_queries(session_id, question, tools)


@pytest.mark.asyncio
async def test_execute_single_query_success(
    query_executor, mock_tool_manager, mock_data_manager
):
    session_id = 1
    question = "测试问题"
    tool_name = "tool1"

    mock_tool_manager.run_tool.return_value = ToolResult(
        tool_name="tool1",
        success=True,
        answer="答案",
        error_message=None,
        execution_time=1.0,
        timestamp=datetime.now().isoformat(),
    )

    result = await query_executor.execute_single_query(session_id, question, tool_name)

    assert result.tool_name == tool_name
    assert result.success is True
    assert mock_data_manager.save_tool_result.call_count == 1


@pytest.mark.asyncio
async def test_execute_single_query_exception(query_executor, mock_tool_manager):
    session_id = 1
    question = "测试问题"
    tool_name = "tool1"

    mock_tool_manager.run_tool.side_effect = Exception("测试异常")

    with pytest.raises(Exception):
        await query_executor.execute_single_query(session_id, question, tool_name)


def test_get_query_results(query_executor, mock_data_manager):
    session_id = 1

    mock_db_result = Mock()
    mock_db_result.tool_name = "tool1"
    mock_db_result.success = True
    mock_db_result.answer = "答案"
    mock_db_result.error_message = None
    mock_db_result.execution_time = 1.0
    mock_db_result.timestamp = datetime.now()

    mock_data_manager.get_tool_results.return_value = [mock_db_result]

    results = query_executor.get_query_results(session_id)

    assert len(results) == 1
    assert results[0].tool_name == "tool1"
    assert results[0].success is True


def test_validate_query_params_valid(query_executor):
    question = "测试问题"
    tools = ["tool1", "tool2"]

    is_valid, message = query_executor.validate_query_params(question, tools)

    assert is_valid is True
    assert "验证通过" in message


def test_validate_query_params_empty_question(query_executor):
    question = ""
    tools = ["tool1"]

    is_valid, message = query_executor.validate_query_params(question, tools)

    assert is_valid is False
    assert "不能为空" in message


def test_validate_query_params_no_tools(query_executor):
    question = "测试问题"
    tools = []

    is_valid, message = query_executor.validate_query_params(question, tools)

    assert is_valid is False
    assert "至少需要" in message


def test_validate_query_params_invalid_tool(query_executor):
    question = "测试问题"
    tools = ["invalid_tool"]

    is_valid, message = query_executor.validate_query_params(question, tools)

    assert is_valid is False
    assert "不可用" in message


def test_cancel_queries(query_executor):
    session_id = 1

    result = query_executor.cancel_queries(session_id)

    assert result is True

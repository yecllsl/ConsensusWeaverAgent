from unittest.mock import Mock, patch

import pytest

from src.service.interaction.interaction_engine import (
    InteractionEngine,
    InteractionState,
)


@pytest.fixture
def mock_llm_service():
    llm_service = Mock()
    llm_service.analyze_question = Mock(
        return_value={"is_complete": True, "is_clear": True, "ambiguities": []}
    )
    llm_service.generate_clarification_question = Mock(return_value="澄清问题")
    llm_service.refine_question = Mock(return_value="重构问题")
    return llm_service


@pytest.fixture
def mock_data_manager():
    data_manager = Mock()
    data_manager.save_session = Mock(return_value=1)
    data_manager.update_session = Mock()
    data_manager.get_session = Mock(return_value=None)
    data_manager.get_tool_results = Mock(return_value=[])
    return data_manager


@pytest.fixture
def interaction_engine(mock_llm_service, mock_data_manager):
    return InteractionEngine(mock_llm_service, mock_data_manager)


def test_interaction_engine_initialization(
    interaction_engine, mock_llm_service, mock_data_manager
):
    assert interaction_engine.llm_service == mock_llm_service
    assert interaction_engine.data_manager == mock_data_manager
    assert interaction_engine.max_clarification_rounds == 3
    assert interaction_engine.external_agent is None


def test_start_interaction(interaction_engine, mock_data_manager):
    question = "测试问题"

    mock_data_manager.save_session.return_value = 1

    state = interaction_engine.start_interaction(question)

    assert state.session_id == 1
    assert state.original_question == question
    assert state.refined_question is None
    assert state.clarification_rounds == 0
    assert state.completed is False
    assert mock_data_manager.save_session.called


def test_analyze_question(interaction_engine, mock_llm_service):
    state = InteractionState(session_id=1, original_question="测试问题")

    analysis = interaction_engine.analyze_question(state)

    assert analysis["is_complete"] is True
    assert analysis["is_clear"] is True
    assert mock_llm_service.analyze_question.called


def test_analyze_question_exception(interaction_engine, mock_llm_service):
    state = InteractionState(session_id=1, original_question="测试问题")

    mock_llm_service.analyze_question.side_effect = Exception("测试异常")

    with pytest.raises(Exception):
        interaction_engine.analyze_question(state)


def test_generate_clarification_no_need(interaction_engine):
    state = InteractionState(session_id=1, original_question="测试问题")
    analysis = {"is_complete": True, "is_clear": True, "ambiguities": []}

    clarification = interaction_engine.generate_clarification(state, analysis)

    assert clarification is None


def test_generate_clarification_max_rounds(interaction_engine):
    state = InteractionState(
        session_id=1, original_question="测试问题", clarification_rounds=3
    )
    analysis = {"is_complete": False, "is_clear": False, "ambiguities": ["歧义1"]}

    clarification = interaction_engine.generate_clarification(state, analysis)

    assert clarification is None


def test_generate_clarification_success(interaction_engine, mock_llm_service):
    state = InteractionState(session_id=1, original_question="测试问题")
    analysis = {"is_complete": False, "is_clear": False, "ambiguities": ["歧义1"]}

    mock_llm_service.generate_clarification_question.return_value = "这是澄清问题"

    clarification = interaction_engine.generate_clarification(state, analysis)

    assert clarification == "这是澄清问题"
    assert state.clarification_rounds == 1


def test_generate_clarification_exception(interaction_engine, mock_llm_service):
    state = InteractionState(session_id=1, original_question="测试问题")
    analysis = {"is_complete": False, "is_clear": False, "ambiguities": ["歧义1"]}

    mock_llm_service.generate_clarification_question.side_effect = Exception("测试异常")

    with pytest.raises(Exception):
        interaction_engine.generate_clarification(state, analysis)


def test_handle_clarification_response(interaction_engine, mock_data_manager):
    state = InteractionState(session_id=1, original_question="测试问题")
    response = "用户回答"

    updated_state = interaction_engine.handle_clarification_response(state, response)

    assert response in updated_state.clarifications
    assert mock_data_manager.update_session.called


def test_refine_question(interaction_engine, mock_llm_service, mock_data_manager):
    state = InteractionState(session_id=1, original_question="测试问题")

    mock_llm_service.refine_question.return_value = "重构后的问题"

    refined = interaction_engine.refine_question(state)

    assert refined == "重构后的问题"
    assert state.refined_question == "重构后的问题"
    assert mock_data_manager.update_session.called


def test_refine_question_exception(interaction_engine, mock_llm_service):
    state = InteractionState(session_id=1, original_question="测试问题")

    mock_llm_service.refine_question.side_effect = Exception("测试异常")

    with pytest.raises(Exception):
        interaction_engine.refine_question(state)


def test_complete_interaction(interaction_engine, mock_data_manager):
    state = InteractionState(session_id=1, original_question="测试问题")

    completed_state = interaction_engine.complete_interaction(state)

    assert completed_state.completed is True
    assert mock_data_manager.update_session.called


def test_get_session_state_not_found(interaction_engine, mock_data_manager):
    mock_data_manager.get_session.return_value = None

    state = interaction_engine.get_session_state(999)

    assert state is None


def test_get_session_state_found(interaction_engine, mock_data_manager):
    mock_session = Mock()
    mock_session.id = 1
    mock_session.original_question = "测试问题"
    mock_session.refined_question = "重构问题"
    mock_session.completed = True

    mock_data_manager.get_session.return_value = mock_session

    state = interaction_engine.get_session_state(1)

    assert state is not None
    assert state.session_id == 1
    assert state.original_question == "测试问题"
    assert state.completed is True


def test_get_session_state_with_clarifications(interaction_engine, mock_data_manager):
    mock_session = Mock()
    mock_session.id = 1
    mock_session.original_question = "测试问题"
    mock_session.refined_question = None
    mock_session.completed = False

    mock_data_manager.get_session.return_value = mock_session

    mock_clarification_result = Mock()
    mock_clarification_result.tool_name = "clarification"
    mock_clarification_result.answer = "澄清回答"

    mock_data_manager.get_tool_results.return_value = [mock_clarification_result]

    state = interaction_engine.get_session_state(1)

    assert state is not None
    assert len(state.clarifications) == 1
    assert "澄清回答" in state.clarifications


def test_is_clarification_needed_true():
    analysis = {"is_complete": False, "is_clear": True, "ambiguities": []}

    engine = Mock()
    engine.is_clarification_needed = InteractionEngine.is_clarification_needed.__get__(
        engine, InteractionEngine
    )

    result = engine.is_clarification_needed(analysis)

    assert result is True


def test_is_clarification_needed_false():
    analysis = {"is_complete": True, "is_clear": True, "ambiguities": []}

    engine = Mock()
    engine.is_clarification_needed = InteractionEngine.is_clarification_needed.__get__(
        engine, InteractionEngine
    )

    result = engine.is_clarification_needed(analysis)

    assert result is False


def test_interaction_state_creation():
    state = InteractionState(
        session_id=1,
        original_question="测试问题",
        refined_question="重构问题",
        clarification_rounds=2,
        clarifications=["回答1", "回答2"],
        completed=True,
    )

    assert state.session_id == 1
    assert state.original_question == "测试问题"
    assert state.refined_question == "重构问题"
    assert state.clarification_rounds == 2
    assert len(state.clarifications) == 2
    assert state.completed is True


def test_interaction_state_defaults():
    state = InteractionState(session_id=1, original_question="测试问题")

    assert state.session_id == 1
    assert state.original_question == "测试问题"
    assert state.refined_question is None
    assert state.clarification_rounds == 0
    assert state.clarifications == []
    assert state.completed is False


@pytest.mark.unit
def test_interaction_engine_with_external_agent(mock_data_manager):
    mock_external_agent = Mock()
    mock_external_agent.analyze_question = Mock(
        return_value={"is_complete": True, "is_clear": True, "ambiguities": []}
    )

    with patch(
        "src.service.interaction.interaction_engine.create_external_agent"
    ) as mock_create:
        mock_create.return_value = mock_external_agent

        engine = InteractionEngine(
            llm_service=Mock(), data_manager=mock_data_manager, main_agent="test_agent"
        )

        assert engine.external_agent is not None

        state = InteractionState(session_id=1, original_question="测试问题")
        analysis = engine.analyze_question(state)

        assert analysis["is_complete"] is True
        assert mock_external_agent.analyze_question.called

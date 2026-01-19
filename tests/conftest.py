# tests/conftest.py
import pytest
from src.infrastructure.data.data_manager import DataManager


@pytest.fixture(scope="function")
def data_manager():
    """提供内存数据库的数据管理器实例，每个测试函数使用独立的数据库"""
    # 使用内存数据库而不是文件数据库，提高测试速度
    manager = DataManager(":memory:")
    yield manager
    manager.close()


@pytest.fixture(scope="session")
def test_data():
    """提供共享的测试数据，避免重复创建"""
    return {
        "original_question": "什么是人工智能？",
        "refined_question": "人工智能的定义和应用是什么？",
        "similarity_matrix": [[1.0, 0.8], [0.8, 1.0]],
        "consensus_scores": {"iflow": 90.5, "codebuddy": 85.0},
        "key_points": [{
            "content": "人工智能的定义", 
            "sources": ["iflow", "codebuddy"]
        }],
        "differences": [{
            "content": "应用领域的不同观点", 
            "sources": ["iflow", "codebuddy"]
        }],
        "comprehensive_summary": "综合来看，人工智能是一种模拟人类智能的技术...",
        "final_conclusion": "最终结论是，人工智能在多个领域都有广泛应用..."
    }


@pytest.fixture(scope="function")
def mock_llm_service(mocker):
    """模拟LLM服务，避免真实的LLM调用开销"""
    mock_service = mocker.MagicMock()
    mock_service.generate_response.return_value = "模拟的LLM响应"
    mock_service.chat.return_value = "模拟的聊天响应"
    mock_service.analyze_question.return_value = {
        "is_complete": True,
        "is_clear": True,
        "ambiguities": [],
        "complexity": "simple"
    }
    mock_service.generate_clarification_question.return_value = None
    return mock_service


@pytest.fixture(scope="function")
def mock_config_manager(mocker):
    """模拟配置管理器，返回默认配置"""
    mock_manager = mocker.MagicMock()
    mock_manager.get_config.return_value = mocker.MagicMock(
        local_llm=mocker.MagicMock(
            provider="llama-cpp",
            model="test-model.gguf",
            model_path=".models/test-model.gguf",
            n_ctx=4096,
            n_threads=6
        ),
        app=mocker.MagicMock(
            max_clarification_rounds=3,
            log_level="info",
            log_file="test.log"
        )
    )
    return mock_manager

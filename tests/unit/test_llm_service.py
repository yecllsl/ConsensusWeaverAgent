import pytest
import json
from unittest.mock import Mock, patch

from src.infrastructure.llm.llm_service import LLMService
from src.infrastructure.config.config_manager import ConfigManager


@pytest.fixture
def config_manager():
    """创建配置管理器实例"""
    return ConfigManager("config.yaml")


@pytest.fixture
def llm_service(config_manager):
    """创建LLM服务实例"""
    return LLMService(config_manager)


def test_analyze_question_empty_response(llm_service):
    """测试分析问题时LLM返回空响应的情况"""
    # 模拟空响应
    with patch.object(llm_service, "generate_response", return_value=""):
        result = llm_service.analyze_question("人工智能是什么？")

        # 验证返回默认结果
        assert result == {
            "is_complete": True,
            "is_clear": True,
            "ambiguities": [],
            "missing_info": [],
            "complexity": "complex",
        }


def test_analyze_question_invalid_json(llm_service):
    """测试分析问题时LLM返回无效JSON的情况"""
    # 模拟无效JSON响应
    with patch.object(
        llm_service, "generate_response", return_value="这不是有效的JSON格式"
    ):
        result = llm_service.analyze_question("人工智能是什么？")

        # 验证返回默认结果
        assert result == {
            "is_complete": True,
            "is_clear": True,
            "ambiguities": [],
            "missing_info": [],
            "complexity": "complex",
        }


def test_analyze_question_valid_json(llm_service):
    """测试分析问题时LLM返回有效JSON的情况"""
    # 模拟有效JSON响应
    valid_json = """{
        "is_complete": true,
        "is_clear": true,
        "ambiguities": [],
        "missing_info": [],
        "complexity": "complex"
    }"""

    with patch.object(llm_service, "generate_response", return_value=valid_json):
        result = llm_service.analyze_question("人工智能是什么？")

        # 验证返回正确解析的结果
        assert result == {
            "is_complete": True,
            "is_clear": True,
            "ambiguities": [],
            "missing_info": [],
            "complexity": "complex",
        }


def test_analyze_question_with_chinese_commas(llm_service):
    """测试分析问题时LLM返回包含中文逗号的JSON的情况"""
    # 模拟包含中文逗号的JSON响应
    json_with_chinese_commas = """{
        "is_complete": true, 
        "is_clear": false, 
        "ambiguities": ["歧义1"， "歧义2"， "歧义3"], 
        "missing_info": ["信息1"， "信息2"], 
        "complexity": "complex"
    }"""

    with patch.object(
        llm_service, "generate_response", return_value=json_with_chinese_commas
    ):
        result = llm_service.analyze_question("人工智能是什么？")

        # 验证返回正确解析的结果
        assert result == {
            "is_complete": True,
            "is_clear": False,
            "ambiguities": ["歧义1", "歧义2", "歧义3"],
            "missing_info": ["信息1", "信息2"],
            "complexity": "complex",
        }


def test_analyze_question_with_extra_text(llm_service):
    """测试分析问题时LLM返回包含额外文本的JSON的情况"""
    # 模拟包含额外文本的JSON响应
    json_with_extra_text = """{
        "is_complete": true,
        "is_clear": true,
        "ambiguities": [],
        "missing_info": [],
        "complexity": "complex"
    } 这是额外的文本"""

    with patch.object(
        llm_service, "generate_response", return_value=json_with_extra_text
    ):
        result = llm_service.analyze_question("人工智能是什么？")

        # 验证返回正确解析的结果
        assert result == {
            "is_complete": True,
            "is_clear": True,
            "ambiguities": [],
            "missing_info": [],
            "complexity": "complex",
        }


def test_refine_question_with_clarifications(llm_service):
    """测试重构问题时包含澄清信息的情况"""
    # 模拟有效的重构问题响应
    with patch.object(
        llm_service,
        "generate_response",
        return_value="推荐三个适合开发命令行界面形式AI代理的开发框架，并详细说明每个框架的优缺点和适用场景",
    ):
        result = llm_service.refine_question(
            "推荐三个开发cli形式AI Agent的开发框架，并说明他们的优缺点和是和场景",
            ["'是和场景'应为'适用场景'的笔误"],
        )

        # 验证返回正确的重构问题
        assert "开发框架" in result
        assert "优缺点" in result
        assert "适用场景" in result


def test_refine_question_with_prefix(llm_service):
    """测试重构问题时LLM返回包含前缀的响应"""
    # 模拟包含前缀的重构问题响应
    with patch.object(
        llm_service,
        "generate_response",
        return_value="重构后的问题：推荐三个适合开发命令行界面形式AI代理的开发框架，并详细说明每个框架的优缺点和适用场景",
    ):
        result = llm_service.refine_question(
            "推荐三个开发cli形式AI Agent的开发框架，并说明他们的优缺点和是和场景",
            ["'是和场景'应为'适用场景'的笔误"],
        )

        # 验证返回正确的重构问题（没有前缀）
        assert not result.startswith("重构后的问题：")
        assert "开发框架" in result


def test_refine_question_failure(llm_service):
    """测试重构问题失败的情况"""
    # 模拟重构失败
    with patch.object(
        llm_service, "generate_response", side_effect=Exception("LLM生成响应失败")
    ):
        original_question = (
            "推荐三个开发cli形式AI Agent的开发框架，并说明他们的优缺点和是和场景"
        )
        result = llm_service.refine_question(
            original_question, ["'是和场景'应为'适用场景'的笔误"]
        )

        # 验证返回原始问题
        assert result == original_question

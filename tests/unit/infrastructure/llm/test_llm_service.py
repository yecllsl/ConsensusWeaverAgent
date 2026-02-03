from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.llm.llm_service import LLMService


@pytest.fixture
def llm_service():
    """创建模拟的LLM服务实例，避免实际加载模型"""
    # 创建模拟的LLMService实例，不实际初始化模型
    with patch("src.infrastructure.llm.llm_service.LLMService._init_llm"):
        llm_service_instance = LLMService.__new__(LLMService)

        # 手动设置必要的属性
        llm_service_instance.logger = MagicMock()
        llm_service_instance.llm = MagicMock()
        llm_service_instance.chat_llm = MagicMock()
        llm_service_instance.config = MagicMock()

        # 调用__init__方法（会调用_init_llm，但我们已经模拟了它）
        llm_service_instance.__init__(MagicMock())

        # __init__方法会重新设置llm和chat_llm为None，所以需要重新设置
        llm_service_instance.llm = MagicMock()
        llm_service_instance.chat_llm = MagicMock()

        yield llm_service_instance


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
        "ambiguities": ["歧义1", "歧义2", "歧义3"], 
        "missing_info": ["信息1", "信息2"], 
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


@pytest.mark.unit
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


def test_generate_response_success(llm_service):
    """测试成功生成响应"""
    llm_service.llm.invoke.return_value = "测试响应"

    result = llm_service.generate_response("测试提示")

    assert result == "测试响应"
    llm_service.llm.invoke.assert_called_once_with("测试提示")


def test_generate_response_with_string_response(llm_service):
    """测试生成响应返回字符串"""
    llm_service.llm.invoke.return_value = "测试响应"

    result = llm_service.generate_response("测试提示")

    assert isinstance(result, str)
    assert result == "测试响应"


def test_generate_response_with_non_string_response(llm_service):
    """测试生成响应返回非字符串类型"""
    llm_service.llm.invoke.return_value = MagicMock()

    result = llm_service.generate_response("测试提示")

    assert isinstance(result, str)


def test_generate_response_exception_handling(llm_service):
    """测试生成响应异常处理"""
    llm_service.llm.invoke.side_effect = Exception("生成失败")

    with pytest.raises(Exception):
        llm_service.generate_response("测试提示")


def test_chat_with_system_message(llm_service):
    """测试聊天对话包含系统消息"""
    messages = [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"},
    ]

    mock_response = MagicMock()
    mock_response.content = "你好！"
    llm_service.chat_llm.invoke.return_value = mock_response

    result = llm_service.chat(messages)

    assert result == "你好！"
    llm_service.chat_llm.invoke.assert_called_once()


def test_chat_with_user_message(llm_service):
    """测试聊天对话包含用户消息"""
    messages = [{"role": "user", "content": "你好"}]

    mock_response = MagicMock()
    mock_response.content = "你好！"
    llm_service.chat_llm.invoke.return_value = mock_response

    result = llm_service.chat(messages)

    assert result == "你好！"


def test_chat_with_assistant_message(llm_service):
    """测试聊天对话包含助手消息"""
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！"},
        {"role": "user", "content": "再见"},
    ]

    mock_response = MagicMock()
    mock_response.content = "再见！"
    llm_service.chat_llm.invoke.return_value = mock_response

    result = llm_service.chat(messages)

    assert result == "再见！"


def test_chat_with_list_content(llm_service):
    """测试聊天对话返回列表内容"""
    messages = [{"role": "user", "content": "你好"}]

    mock_response = MagicMock()
    mock_response.content = ["你好！"]
    llm_service.chat_llm.invoke.return_value = mock_response

    result = llm_service.chat(messages)

    assert isinstance(result, str)


def test_chat_exception_handling(llm_service):
    """测试聊天对话异常处理"""
    messages = [{"role": "user", "content": "你好"}]

    llm_service.chat_llm.invoke.side_effect = Exception("聊天失败")

    with pytest.raises(Exception):
        llm_service.chat(messages)


def test_generate_clarification_question_success(llm_service):
    """测试成功生成澄清问题"""
    analysis = {
        "is_complete": False,
        "is_clear": False,
        "ambiguities": ["歧义"],
        "missing_info": ["缺失信息"],
        "complexity": "complex",
    }

    with patch.object(
        llm_service, "generate_response", return_value="您想了解哪个方面？"
    ):
        result = llm_service.generate_clarification_question("测试问题", analysis)

        assert result == "您想了解哪个方面？"


def test_generate_clarification_question_exception_handling(llm_service):
    """测试生成澄清问题异常处理"""
    analysis = {
        "is_complete": False,
        "is_clear": False,
        "ambiguities": ["歧义"],
        "missing_info": ["缺失信息"],
        "complexity": "complex",
    }

    with patch.object(
        llm_service, "generate_response", side_effect=Exception("生成失败")
    ):
        with pytest.raises(Exception):
            llm_service.generate_clarification_question("测试问题", analysis)


def test_classify_question_complexity_simple(llm_service):
    """测试判断问题为简单问题"""
    with patch.object(llm_service, "generate_response", return_value="simple"):
        result = llm_service.classify_question_complexity("什么是Python？")

        assert result == "simple"


def test_classify_question_complexity_complex(llm_service):
    """测试判断问题为复杂问题"""
    with patch.object(llm_service, "generate_response", return_value="complex"):
        result = llm_service.classify_question_complexity("比较Python和Java")

        assert result == "complex"


def test_classify_question_complexity_mixed_case(llm_service):
    """测试判断问题复杂度（混合大小写）"""
    with patch.object(llm_service, "generate_response", return_value="Simple"):
        result = llm_service.classify_question_complexity("测试问题")

        assert result == "simple"


def test_classify_question_complexity_exception_handling(llm_service):
    """测试判断问题复杂度异常处理"""
    with patch.object(
        llm_service, "generate_response", side_effect=Exception("判断失败")
    ):
        with pytest.raises(Exception):
            llm_service.classify_question_complexity("测试问题")


def test_answer_simple_question_success(llm_service):
    """测试成功回答简单问题"""
    with patch.object(
        llm_service, "generate_response", return_value="Python是一种编程语言"
    ):
        result = llm_service.answer_simple_question("什么是Python？")

        assert result == "Python是一种编程语言"


def test_answer_simple_question_exception_handling(llm_service):
    """测试回答简单问题异常处理"""
    with patch.object(
        llm_service, "generate_response", side_effect=Exception("回答失败")
    ):
        with pytest.raises(Exception):
            llm_service.answer_simple_question("测试问题")


def test_update_config(llm_service):
    """测试更新配置"""
    mock_config_manager = MagicMock()
    mock_config = MagicMock()
    mock_local_llm = MagicMock()
    mock_config.local_llm = mock_local_llm
    mock_config_manager.get_config.return_value = mock_config

    with patch.object(llm_service, "_init_llm"):
        llm_service.update_config(mock_config_manager)

        assert llm_service.config == mock_local_llm

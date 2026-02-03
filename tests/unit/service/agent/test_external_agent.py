"""测试外部Agent模块"""

import json
from unittest.mock import MagicMock, patch


class TestExternalAgent:
    """测试ExternalAgent类"""

    def test_initialization(self):
        """测试Agent初始化"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")
        assert agent.agent_name == "iflow"

    def test_initialization_with_different_agents(self):
        """测试不同Agent的初始化"""
        from src.service.agent.external_agent import ExternalAgent

        agents = ["iflow", "qwen", "codebuddy"]
        for agent_name in agents:
            agent = ExternalAgent(agent_name)
            assert agent.agent_name == agent_name

    def test_analyze_question_success(self):
        """测试成功分析问题"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")

        mock_result = json.dumps(
            {
                "is_complete": True,
                "is_clear": True,
                "ambiguities": [],
                "missing_info": [],
            }
        )

        with patch.object(agent, "_execute_tool", return_value=mock_result):
            result = agent.analyze_question("什么是Python？")

            assert result["is_complete"] is True
            assert result["is_clear"] is True
            assert result["ambiguities"] == []
            assert result["missing_info"] == []

    def test_analyze_question_with_ambiguities(self):
        """测试分析有歧义的问题"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("qwen")

        mock_result = json.dumps(
            {
                "is_complete": False,
                "is_clear": False,
                "ambiguities": ["是否需要考虑商业用途？"],
                "missing_info": ["具体的应用场景"],
            }
        )

        with patch.object(agent, "_execute_tool", return_value=mock_result):
            result = agent.analyze_question("如何使用Python？")

            assert result["is_complete"] is False
            assert result["is_clear"] is False
            assert len(result["ambiguities"]) > 0
            assert len(result["missing_info"]) > 0

    def test_analyze_question_exception_handling(self):
        """测试分析问题异常处理"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("codebuddy")

        with patch.object(agent, "_execute_tool", side_effect=Exception("执行失败")):
            result = agent.analyze_question("测试问题")

            assert result["is_complete"] is True
            assert result["is_clear"] is True
            assert result["ambiguities"] == []
            assert result["missing_info"] == []

    def test_analyze_question_empty_result(self):
        """测试空结果处理"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")

        with patch.object(agent, "_execute_tool", return_value=""):
            result = agent.analyze_question("测试问题")

            assert result["is_complete"] is True
            assert result["is_clear"] is True

    def test_generate_clarification_question_success(self):
        """测试成功生成澄清问题"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")

        analysis = {
            "is_complete": False,
            "is_clear": False,
            "ambiguities": ["是否需要考虑商业用途？"],
            "missing_info": ["具体的应用场景"],
        }

        with patch.object(
            agent, "_execute_tool", return_value="您想了解Python的哪个方面？"
        ):
            clarification = agent.generate_clarification_question(
                "如何使用Python？", analysis
            )

            assert clarification is not None
            assert "Python" in clarification

    def test_generate_clarification_question_no_ambiguities(self):
        """测试无歧义时的澄清问题生成"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("qwen")

        analysis = {
            "is_complete": True,
            "is_clear": True,
            "ambiguities": [],
            "missing_info": [],
        }

        with patch.object(agent, "_execute_tool", return_value=""):
            clarification = agent.generate_clarification_question(
                "什么是Python？", analysis
            )

            assert clarification is None

    def test_generate_clarification_question_exception_handling(self):
        """测试澄清问题生成异常处理"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("codebuddy")

        analysis = {
            "is_complete": False,
            "is_clear": False,
            "ambiguities": ["歧义"],
            "missing_info": ["缺失信息"],
        }

        with patch.object(agent, "_execute_tool", side_effect=Exception("执行失败")):
            clarification = agent.generate_clarification_question("测试问题", analysis)

            assert clarification is None

    def test_refine_question_success(self):
        """测试成功重构问题"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")

        clarifications = ["我想了解Python的Web开发功能"]

        with patch.object(
            agent, "_execute_tool", return_value="如何使用Python进行Web开发？"
        ):
            refined = agent.refine_question("如何使用Python？", clarifications)

            assert "Web开发" in refined

    def test_refine_question_empty_clarifications(self):
        """测试空澄清列表时的重构"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("qwen")

        with patch.object(agent, "_execute_tool", return_value=""):
            refined = agent.refine_question("如何使用Python？", [])

            assert refined == "如何使用Python？"

    def test_refine_question_exception_handling(self):
        """测试重构问题异常处理"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("codebuddy")

        with patch.object(agent, "_execute_tool", side_effect=Exception("执行失败")):
            refined = agent.refine_question("测试问题", ["澄清信息"])

            assert refined == "测试问题"

    def test_classify_question_complexity_simple(self):
        """测试简单问题分类"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")

        with patch.object(agent, "_execute_tool", return_value="simple"):
            complexity = agent.classify_question_complexity("什么是Python？")

            assert complexity == "simple"

    def test_classify_question_complexity_complex(self):
        """测试复杂问题分类"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("qwen")

        with patch.object(agent, "_execute_tool", return_value="complex"):
            complexity = agent.classify_question_complexity("比较Python和Java的优缺点")

            assert complexity == "complex"

    def test_classify_question_complexity_invalid_response(self):
        """测试无效响应时的分类"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("codebuddy")

        with patch.object(agent, "_execute_tool", return_value="invalid"):
            complexity = agent.classify_question_complexity("测试问题")

            assert complexity == "complex"

    def test_classify_question_complexity_exception_handling(self):
        """测试分类异常处理"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")

        with patch.object(agent, "_execute_tool", side_effect=Exception("执行失败")):
            complexity = agent.classify_question_complexity("测试问题")

            assert complexity == "complex"

    def test_answer_simple_question_success(self):
        """测试成功回答简单问题"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("qwen")

        with patch.object(
            agent, "_execute_tool", return_value="Python是一种高级编程语言"
        ):
            answer = agent.answer_simple_question("什么是Python？")

            assert "Python" in answer

    def test_answer_simple_question_empty_response(self):
        """测试空响应处理"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("codebuddy")

        with patch.object(agent, "_execute_tool", return_value=""):
            answer = agent.answer_simple_question("测试问题")

            assert answer == "无法回答该问题"

    def test_answer_simple_question_exception_handling(self):
        """测试回答问题异常处理"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")

        with patch.object(agent, "_execute_tool", side_effect=Exception("执行失败")):
            answer = agent.answer_simple_question("测试问题")

            assert answer == "无法回答该问题"


class TestExecuteTool:
    """测试工具执行功能"""

    def test_execute_tool_iflow(self):
        """测试执行iflow工具"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")

        mock_result = MagicMock()
        mock_result.stdout = "测试响应".encode("utf-8")
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            result = agent._execute_tool("测试提示")

            assert result == "测试响应"

    def test_execute_tool_qwen(self):
        """测试执行qwen工具"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("qwen")

        mock_result = MagicMock()
        mock_result.stdout = "测试响应".encode("utf-8")
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            result = agent._execute_tool("测试提示")

            assert result == "测试响应"

    def test_execute_tool_codebuddy(self):
        """测试执行codebuddy工具"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("codebuddy")

        mock_result = MagicMock()
        mock_result.stdout = "测试响应".encode("utf-8")
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            result = agent._execute_tool("测试提示")

            assert result == "测试响应"

    def test_execute_tool_invalid_agent(self):
        """测试无效Agent名称"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("invalid_agent")

        result = agent._execute_tool("测试提示")

        assert result == ""

    def test_execute_tool_utf8_encoding(self):
        """测试UTF-8编码处理"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")

        mock_result = MagicMock()
        mock_result.stdout = "测试响应".encode("utf-8")
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            result = agent._execute_tool("测试提示")

            assert result == "测试响应"

    def test_execute_tool_gbk_encoding(self):
        """测试GBK编码处理"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("qwen")

        mock_result = MagicMock()
        mock_result.stdout = "测试响应".encode("gbk")
        mock_result.stderr = b""

        with patch("subprocess.run", return_value=mock_result):
            result = agent._execute_tool("测试提示")

            assert result == "测试响应"

    def test_execute_tool_with_stderr(self):
        """测试处理stderr输出"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("codebuddy")

        mock_result = MagicMock()
        mock_result.stdout = "测试响应".encode("utf-8")
        mock_result.stderr = "警告信息".encode("utf-8")

        with patch("subprocess.run", return_value=mock_result):
            result = agent._execute_tool("测试提示")

            assert result == "测试响应"

    def test_execute_tool_exception_handling(self):
        """测试执行异常处理"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")

        with patch("subprocess.run", side_effect=Exception("执行失败")):
            result = agent._execute_tool("测试提示")

            assert result == ""


class TestParseResult:
    """测试结果解析功能"""

    def test_parse_result_valid_json(self):
        """测试解析有效JSON"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")

        result = json.dumps(
            {
                "is_complete": True,
                "is_clear": True,
                "ambiguities": [],
                "missing_info": [],
            }
        )

        parsed = agent._parse_result(result)

        assert parsed["is_complete"] is True
        assert parsed["is_clear"] is True

    def test_parse_result_empty_string(self):
        """测试解析空字符串"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("qwen")

        parsed = agent._parse_result("")

        assert parsed["is_complete"] is True
        assert parsed["is_clear"] is True

    def test_parse_result_with_text_prefix(self):
        """测试解析带文本前缀的JSON"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("codebuddy")

        result = "分析结果如下：\n" + json.dumps(
            {
                "is_complete": True,
                "is_clear": True,
                "ambiguities": [],
                "missing_info": [],
            }
        )

        parsed = agent._parse_result(result)

        assert parsed["is_complete"] is True

    def test_parse_result_invalid_json(self):
        """测试解析无效JSON"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("iflow")

        parsed = agent._parse_result("这不是一个有效的JSON")

        assert parsed["is_complete"] is True
        assert parsed["is_clear"] is True

    def test_parse_result_partial_json(self):
        """测试解析部分JSON"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("qwen")

        result = '一些文本\n{"is_complete": true}\n更多文本'

        parsed = agent._parse_result(result)

        assert parsed["is_complete"] is True

    def test_parse_result_nested_json(self):
        """测试解析嵌套JSON"""
        from src.service.agent.external_agent import ExternalAgent

        agent = ExternalAgent("codebuddy")

        result = json.dumps(
            {
                "is_complete": True,
                "is_clear": True,
                "ambiguities": ["歧义1", "歧义2"],
                "missing_info": ["缺失1", "缺失2"],
            }
        )

        parsed = agent._parse_result(result)

        assert len(parsed["ambiguities"]) == 2
        assert len(parsed["missing_info"]) == 2


class TestCreateExternalAgent:
    """测试创建外部Agent工厂函数"""

    def test_create_external_agent(self):
        """测试创建外部Agent"""
        from src.service.agent.external_agent import create_external_agent

        agent = create_external_agent("iflow")

        assert agent.agent_name == "iflow"

    def test_create_external_agent_with_different_names(self):
        """测试创建不同名称的外部Agent"""
        from src.service.agent.external_agent import create_external_agent

        agents = ["iflow", "qwen", "codebuddy"]
        for agent_name in agents:
            agent = create_external_agent(agent_name)
            assert agent.agent_name == agent_name

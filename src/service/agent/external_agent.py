import json
import subprocess
import time
from typing import Any, Dict, Optional

from src.infrastructure.logging.logger import get_logger


class ExternalAgent:
    """外部工具作为主Agent的实现"""

    def __init__(self, agent_name: str):
        """初始化外部Agent

        Args:
            agent_name: 外部Agent名称，如"iflow", "qwen", "codebuddy"
        """
        self.agent_name = agent_name
        self.logger = get_logger()
        self.logger.info(f"初始化外部Agent: {agent_name}")

    def analyze_question(self, question: str) -> Dict[str, Any]:
        """分析问题

        Args:
            question: 原始问题

        Returns:
            问题分析结果，包含完整性、清晰度、歧义等信息
        """
        try:
            prompt = (
                f"请分析以下问题的完整性、清晰度和潜在歧义：\n\n"
                f"问题：{question}\n\n"
                f"请按照以下JSON格式返回分析结果：\n"
                f"{{\n"
                f'  "is_complete": true/false,  // 问题是否完整\n'
                f'  "is_clear": true/false,    // 问题是否清晰\n'
                f'  "ambiguities": [],         // 潜在歧义列表\n'
                f'  "missing_info": []         // 缺失信息列表\n'
                f"}}"
            )

            result = self._execute_tool(prompt)
            analysis = self._parse_result(result)

            # 确保返回格式正确
            return {
                "is_complete": analysis.get("is_complete", True),
                "is_clear": analysis.get("is_clear", True),
                "ambiguities": analysis.get("ambiguities", []),
                "missing_info": analysis.get("missing_info", []),
            }
        except Exception as e:
            self.logger.error(f"分析问题失败: {e}")
            # 返回默认分析结果
            return {
                "is_complete": True,
                "is_clear": True,
                "ambiguities": [],
                "missing_info": [],
            }

    def generate_clarification_question(
        self, question: str, analysis: Dict[str, Any]
    ) -> Optional[str]:
        """生成澄清问题

        Args:
            question: 原始问题
            analysis: 问题分析结果

        Returns:
            澄清问题，如果不需要澄清则返回None
        """
        try:
            # 准备分析结果文本
            completeness = "完整" if analysis["is_complete"] else "不完整"
            clarity = "清晰" if analysis["is_clear"] else "不清晰"
            ambiguities = (
                ", ".join(analysis["ambiguities"]) if analysis["ambiguities"] else "无"
            )
            missing_info = (
                ", ".join(analysis["missing_info"])
                if analysis["missing_info"]
                else "无"
            )

            prompt = (
                f"基于以下问题和分析结果，生成一个澄清问题：\n\n"
                f"问题：{question}\n\n"
                f"分析结果：\n"
                f"- 完整性：{completeness}\n"
                f"- 清晰度：{clarity}\n"
                f"- 潜在歧义：{ambiguities}\n"
                f"- 缺失信息：{missing_info}\n"
                f"\n"
                f"请生成一个针对性的澄清问题，帮助用户完善问题。\n"
                f"只返回澄清问题本身，不要包含任何其他内容。"
            )

            result = self._execute_tool(prompt)
            return result.strip() if result else None
        except Exception as e:
            self.logger.error(f"生成澄清问题失败: {e}")
            return None

    def refine_question(self, original_question: str, clarifications: list[str]) -> str:
        """重构问题

        Args:
            original_question: 原始问题
            clarifications: 澄清信息列表

        Returns:
            重构后的问题
        """
        try:
            clarifications_text = "\n".join(clarifications) if clarifications else "无"
            prompt = (
                f"基于原始问题和澄清信息，重构一个完整、清晰的问题：\n\n"
                f"原始问题：{original_question}\n\n"
                f"澄清信息：{clarifications_text}\n\n"
                f"请生成一个专业、完整的问题陈述，准确反映用户的意图。\n"
                f"只返回重构后的问题，不要包含任何其他内容。"
            )

            result = self._execute_tool(prompt)
            return result.strip() if result else original_question
        except Exception as e:
            self.logger.error(f"重构问题失败: {e}")
            return original_question

    def classify_question_complexity(self, question: str) -> str:
        """判断问题复杂度

        Args:
            question: 问题文本

        Returns:
            复杂度类别："simple" 或 "complex"
        """
        try:
            prompt = (
                f"判断以下问题的复杂度：\n\n"
                f"问题：{question}\n\n"
                f"简单问题定义：常识性问题、定义性问题、本地知识可回答的问题\n"
                f"复杂问题定义：需要专业领域知识、实时信息、多源验证的问题\n\n"
                f"请只返回 'simple' 或 'complex'，不要包含任何其他内容。"
            )

            result = self._execute_tool(prompt)
            complexity = result.strip().lower()
            return complexity if complexity in ["simple", "complex"] else "complex"
        except Exception as e:
            self.logger.error(f"判断问题复杂度失败: {e}")
            return "complex"

    def answer_simple_question(self, question: str) -> str:
        """回答简单问题

        Args:
            question: 简单问题

        Returns:
            问题答案
        """
        try:
            result = self._execute_tool(question)
            return result.strip() if result else "无法回答该问题"
        except Exception as e:
            self.logger.error(f"回答问题失败: {e}")
            return "无法回答该问题"

    def _execute_tool(self, prompt: str) -> str:
        """执行外部工具

        Args:
            prompt: 提示文本

        Returns:
            工具执行结果
        """
        try:
            start_time = time.time()
            self.logger.info(
                f"执行外部Agent {self.agent_name}，提示长度: {len(prompt)}"
            )

            # 根据不同的Agent名称执行不同的命令
            if self.agent_name == "iflow":
                cmd = [
                    "powershell.exe",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    f"iflow -y -p '{prompt}'",
                ]
            elif self.agent_name == "qwen":
                cmd = [
                    "powershell.exe",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    f"qwen.ps1 -p '{prompt}'",
                ]
            elif self.agent_name == "codebuddy":
                cmd = [
                    "powershell.exe",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    f"codebuddy.ps1 -p '{prompt}'",
                ]
            else:
                raise ValueError(f"不支持的Agent名称: {self.agent_name}")

            # 执行命令（使用bytes模式捕获输出，手动处理编码）
            result = subprocess.run(cmd, capture_output=True, timeout=60)

            # 尝试使用UTF-8编码解码，失败则使用GBK
            try:
                output = result.stdout.decode("utf-8").strip()
            except UnicodeDecodeError:
                try:
                    output = result.stdout.decode("gbk").strip()
                except UnicodeDecodeError:
                    output = result.stdout.decode("latin-1").strip()

            # 处理stderr
            if result.stderr:
                try:
                    stderr_output = result.stderr.decode("utf-8").strip()
                except UnicodeDecodeError:
                    stderr_output = result.stderr.decode("gbk").strip()
                self.logger.warning(f"工具执行警告: {stderr_output}")

            execution_time = time.time() - start_time
            self.logger.info(
                f"外部Agent {self.agent_name} 执行完成，耗时: {execution_time:.2f}秒"
            )

            return output
        except Exception as e:
            self.logger.error(f"执行外部工具失败: {e}")
            return ""

    def _parse_result(self, result: str) -> Dict[str, Any]:
        """解析工具执行结果

        Args:
            result: 工具执行结果

        Returns:
            解析后的结果
        """
        try:
            if not result:
                return {
                    "is_complete": True,
                    "is_clear": True,
                    "ambiguities": [],
                    "missing_info": [],
                }

            # 清理结果字符串
            cleaned_result = result.strip()

            # 尝试直接解析JSON
            try:
                parsed: Dict[str, Any] = json.loads(cleaned_result)
                return parsed
            except json.JSONDecodeError:
                # 尝试提取JSON部分
                # 查找JSON开始和结束位置
                start_pos = cleaned_result.find("{")
                if start_pos == -1:
                    start_pos = cleaned_result.find("[")

                if start_pos != -1:
                    # 尝试找到对应的结束位置
                    if cleaned_result[start_pos] == "{":
                        # 处理对象
                        brace_count = 0
                        end_pos = -1
                        for i in range(start_pos, len(cleaned_result)):
                            if cleaned_result[i] == "{":
                                brace_count += 1
                            elif cleaned_result[i] == "}":
                                brace_count -= 1
                                if brace_count == 0:
                                    end_pos = i + 1
                                    break
                    else:
                        # 处理数组
                        bracket_count = 0
                        end_pos = -1
                        for i in range(start_pos, len(cleaned_result)):
                            if cleaned_result[i] == "[":
                                bracket_count += 1
                            elif cleaned_result[i] == "]":
                                bracket_count -= 1
                                if bracket_count == 0:
                                    end_pos = i + 1
                                    break

                    if end_pos != -1:
                        json_part = cleaned_result[start_pos:end_pos]
                        try:
                            extracted_parsed: Dict[str, Any] = json.loads(json_part)
                            return extracted_parsed
                        except json.JSONDecodeError:
                            self.logger.warning(
                                f"提取的JSON部分解析失败: {json_part[:100]}..."
                            )

            # 如果不是JSON格式，返回默认结果
            self.logger.warning(
                f"外部Agent返回非JSON格式结果: {cleaned_result[:100]}..."
            )
            return {
                "is_complete": True,
                "is_clear": True,
                "ambiguities": [],
                "missing_info": [],
            }
        except Exception as e:
            self.logger.error(f"解析结果失败: {e}")
            return {
                "is_complete": True,
                "is_clear": True,
                "ambiguities": [],
                "missing_info": [],
            }


def create_external_agent(agent_name: str) -> ExternalAgent:
    """创建外部Agent实例

    Args:
        agent_name: 外部Agent名称

    Returns:
        ExternalAgent实例
    """
    return ExternalAgent(agent_name)

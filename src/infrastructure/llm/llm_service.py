from typing import Any, Dict, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_community.chat_models import ChatLlamaCpp
from langchain_community.llms import LlamaCpp

from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.logging.logger import get_logger


class LLMService:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.get_config().local_llm
        self.logger = get_logger()
        self.llm = None
        self.chat_llm = None
        self._init_llm()

    def _init_llm(self) -> None:
        """初始化LLM连接"""
        try:
            # 初始化基础LLM
            self.llm = LlamaCpp(
                model_path=self.config.model_path,
                n_ctx=self.config.n_ctx,
                n_threads=self.config.n_threads,
                temperature=self.config.temperature
            )
            
            # 初始化聊天LLM
            self.chat_llm = ChatLlamaCpp(
                model_path=self.config.model_path,
                n_ctx=self.config.n_ctx,
                n_threads=self.config.n_threads,
                temperature=self.config.temperature
            )
            
            self.logger.info(f"成功加载本地模型: {self.config.model}")
        except Exception as e:
            self.logger.error(f"加载本地模型失败: {e}")
            raise

    def generate_response(self, prompt: str) -> str:
        """生成LLM响应"""
        try:
            response = self.llm.invoke(prompt)
            return response.strip()
        except Exception as e:
            self.logger.error(f"LLM生成响应失败: {e}")
            raise

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """进行聊天对话"""
        try:
            # 转换消息格式
            chat_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    chat_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    chat_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    chat_messages.append(AIMessage(content=msg["content"]))
            
            # 调用聊天LLM
            response = self.chat_llm.invoke(chat_messages)
            return response.content.strip()
        except Exception as e:
            self.logger.error(f"LLM聊天对话失败: {e}")
            raise

    def analyze_question(self, question: str) -> Dict[str, Any]:
        """分析问题的完整性、清晰度和潜在歧义"""
        try:
            import json
            
            prompt = f"""
            请分析以下问题的完整性、清晰度和潜在歧义：
            "{question}"
            
            请严格按照以下JSON格式返回分析结果，不要添加任何额外的解释或说明文字，只返回JSON字符串：
            {{"is_complete": true/false, "is_clear": true/false, "ambiguities": ["歧义1", "歧义2"], "missing_info": ["信息1", "信息2"], "complexity": "simple"/"complex"}}
            
            注意：
            1. 只返回JSON字符串，不要包含任何其他内容
            2. 使用英文逗号分隔字段
            3. 布尔值使用true/false，字符串使用双引号
            """
            
            response = self.generate_response(prompt)
            self.logger.debug(f"LLM原始响应: '{response}'")
            
            if not response.strip():
                self.logger.error("LLM返回了空响应")
                # 返回默认的分析结果
                return {
                    "is_complete": True,
                    "is_clear": True,
                    "ambiguities": [],
                    "missing_info": [],
                    "complexity": "complex"
                }
            
            # 替换中文逗号为英文逗号，提高兼容性
            response = response.replace('，', ',')
            self.logger.debug(f"处理后响应: '{response}'")
            
            # 尝试从响应中提取JSON部分
            try:
                # 找到JSON的开始和结束位置
                start_pos = response.find('{')
                end_pos = response.rfind('}') + 1
                
                if start_pos != -1 and end_pos != -1:
                    # 提取JSON部分
                    json_str = response[start_pos:end_pos]
                    self.logger.debug(f"提取的JSON部分: '{json_str}'")
                    # 使用安全的JSON解析替代eval
                    return json.loads(json_str)
                else:
                    # 如果没有找到JSON结构，尝试直接解析整个响应
                    return json.loads(response)
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败，响应内容: '{response}'，错误: {e}")
                # 返回默认的分析结果
                return {
                    "is_complete": True,
                    "is_clear": True,
                    "ambiguities": [],
                    "missing_info": [],
                    "complexity": "complex"
                }
        except Exception as e:
            self.logger.error(f"LLM分析问题失败: {e}")
            raise

    def generate_clarification_question(self, original_question: str, analysis: Dict[str, Any]) -> str:
        """根据问题分析生成澄清问题"""
        try:
            prompt = f"""
            请根据以下问题分析结果，生成一个针对性的澄清问题：
            
            原始问题："{original_question}"
            
            问题分析：
            - 完整性：{'完整' if analysis['is_complete'] else '不完整'}
            - 清晰度：{'清晰' if analysis['is_clear'] else '不清晰'}
            - 潜在歧义：{', '.join(analysis['ambiguities']) if analysis['ambiguities'] else '无'}
            - 缺失信息：{', '.join(analysis['missing_info']) if analysis['missing_info'] else '无'}
            - 复杂度：{analysis['complexity']}
            
            请生成一个简洁、明确的澄清问题，帮助用户完善问题。
            """
            
            return self.generate_response(prompt)
        except Exception as e:
            self.logger.error(f"LLM生成澄清问题失败: {e}")
            raise

    def refine_question(self, original_question: str, clarifications: List[str]) -> str:
        """根据原始问题和澄清信息重构问题"""
        try:
            prompt = f"""
            请严格按照以下要求重构问题：
            
            原始问题："{original_question}"
            
            澄清信息：
            {chr(10).join([f"- {clarification}" for clarification in clarifications])}
            
            重构要求：
            1. 只返回重构后的问题，不要添加任何额外的解释或说明文字
            2. 重构后的问题要专业、完整，准确反映用户的核心意图
            3. 包含所有必要信息，且清晰无歧义
            4. 不要重复原始问题和澄清信息的内容
            """
            
            response = self.generate_response(prompt)
            # 清理响应，只保留问题部分
            response = response.strip()
            # 移除可能的前缀
            if response.startswith("重构后的问题："):
                response = response[7:].strip()
            return response
        except Exception as e:
            self.logger.error(f"LLM重构问题失败: {e}")
            # 如果重构失败，返回原始问题
            return original_question

    def classify_question_complexity(self, question: str) -> str:
        """判断问题复杂度（简单或复杂）"""
        try:
            prompt = f"""
            请判断以下问题的复杂度：
            "{question}"
            
            复杂度定义：
            - 简单问题：常识性问题、定义性问题、本地知识可回答的问题
            - 复杂问题：需要专业领域知识、实时信息、多源验证的问题
            
            请直接返回"simple"或"complex"。
            """
            
            response = self.generate_response(prompt)
            return response.strip().lower()
        except Exception as e:
            self.logger.error(f"LLM判断问题复杂度失败: {e}")
            raise

    def answer_simple_question(self, question: str) -> str:
        """回答简单问题"""
        try:
            prompt = f"""
            请回答以下问题：
            "{question}"
            
            请提供简洁、准确的答案，避免不必要的解释。
            """
            
            return self.generate_response(prompt)
        except Exception as e:
            self.logger.error(f"LLM回答简单问题失败: {e}")
            raise

    def update_config(self, config_manager: ConfigManager) -> None:
        """更新LLM配置"""
        self.config = config_manager.get_config().local_llm
        self._init_llm()

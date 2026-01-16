from typing import Any, Dict, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_community.llms import Ollama

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
            self.llm = Ollama(
                base_url=self.config.base_url,
                model=self.config.model,
                timeout=self.config.timeout,
                temperature=0.3
            )
            
            # 初始化聊天LLM
            self.chat_llm = ChatOllama(
                base_url=self.config.base_url,
                model=self.config.model,
                timeout=self.config.timeout,
                temperature=0.3
            )
            
            self.logger.info(f"成功连接到本地LLM服务: {self.config.model}")
        except Exception as e:
            self.logger.error(f"连接本地LLM服务失败: {e}")
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
            prompt = f"""
            请分析以下问题的完整性、清晰度和潜在歧义：
            "{question}"
            
            请以JSON格式返回分析结果，包含以下字段：
            - is_complete: boolean，表示问题是否完整（包含必要信息）
            - is_clear: boolean，表示问题是否清晰易懂
            - ambiguities: array，表示潜在的歧义点（如果有）
            - missing_info: array，表示缺失的必要信息（如果有）
            - complexity: string，表示问题复杂度（"simple"或"complex"）
            """
            
            response = self.generate_response(prompt)
            return eval(response)  # 注意：在生产环境中应使用更安全的JSON解析
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
            请根据以下原始问题和澄清信息，重构一个专业、完整的最终问题陈述：
            
            原始问题："{original_question}"
            
            澄清信息：
            {chr(10).join([f"- {clarification}" for clarification in clarifications])}
            
            请确保重构后的问题准确反映用户的核心意图，包含所有必要信息，且清晰无歧义。
            """
            
            return self.generate_response(prompt)
        except Exception as e:
            self.logger.error(f"LLM重构问题失败: {e}")
            raise

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

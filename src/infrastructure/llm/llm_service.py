from typing import Any, Dict, List, Optional, cast

from langchain_community.chat_models import ChatLlamaCpp
from langchain_community.llms import LlamaCpp
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.logging.logger import get_logger


class LLMService:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.get_config().local_llm
        self.logger = get_logger()
        self.llm: Optional[LlamaCpp] = None
        self.chat_llm: Optional[ChatLlamaCpp] = None
        self._init_llm()

    def _init_llm(self) -> None:
        """初始化LLM连接"""
        try:
            # 初始化基础LLM
            self.llm = LlamaCpp(
                model_path=cast(str, self.config.model_path),
                n_ctx=self.config.n_ctx,
                n_threads=self.config.n_threads,
                n_batch=self.config.n_batch,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                repeat_penalty=self.config.repeat_penalty,
                last_n_tokens_size=self.config.last_n_tokens_size,
                use_mlock=self.config.use_mlock,
                use_mmap=self.config.use_mmap,
                n_gpu_layers=self.config.n_gpu_layers,
                rope_freq_base=self.config.rope_freq_base,
                rope_freq_scale=self.config.rope_freq_scale,
                temperature=self.config.temperature,
                model_kwargs={"n_threads_batch": self.config.n_threads_batch},
            )

            # 初始化聊天LLM
            self.chat_llm = ChatLlamaCpp(
                model_path=cast(str, self.config.model_path),
                n_ctx=self.config.n_ctx,
                n_threads=self.config.n_threads,
                n_batch=self.config.n_batch,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                repeat_penalty=self.config.repeat_penalty,
                last_n_tokens_size=self.config.last_n_tokens_size,
                use_mlock=self.config.use_mlock,
                use_mmap=self.config.use_mmap,
                n_gpu_layers=self.config.n_gpu_layers,
                rope_freq_base=self.config.rope_freq_base,
                rope_freq_scale=self.config.rope_freq_scale,
                temperature=self.config.temperature,
                model_kwargs={"n_threads_batch": self.config.n_threads_batch},
            )

            self.logger.info(f"成功加载本地模型: {self.config.model}")
        except Exception as e:
            self.logger.error(f"加载本地模型失败: {e}")
            raise

    def generate_response(self, prompt: str) -> str:
        """生成LLM响应"""
        try:
            # 类型断言：llm在_init_llm中已初始化，不会为None
            llm = cast(LlamaCpp, self.llm)
            response = llm.invoke(prompt)
            # 确保返回str类型，处理response可能是不同类型的情况
            if isinstance(response, str):
                return response.strip()
            else:
                return str(response)
        except Exception as e:
            self.logger.error(f"LLM生成响应失败: {e}")
            raise

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """进行聊天对话"""
        try:
            # 转换消息格式
            chat_messages: List[BaseMessage] = []
            for msg in messages:
                if msg["role"] == "system":
                    chat_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    chat_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    chat_messages.append(AIMessage(content=msg["content"]))

            # 调用聊天LLM
            # 类型断言：chat_llm在_init_llm中已初始化，不会为None
            chat_llm = cast(ChatLlamaCpp, self.chat_llm)
            response = chat_llm.invoke(chat_messages)
            # 确保返回str类型，处理response.content可能是列表的情况
            content = response.content
            if isinstance(content, str):
                return content.strip()
            else:
                return str(content)
        except Exception as e:
            self.logger.error(f"LLM聊天对话失败: {e}")
            raise

    def analyze_question(self, question: str) -> Dict[str, Any]:
        """分析问题的完整性、清晰度和潜在歧义"""
        try:
            import json
            import re

            prompt = f"""
            任务：请仅返回JSON格式的问题分析结果，不要添加任何其他内容。
            
            问题："{question}"
            
            分析内容：
            - is_complete: 问题是否完整 (true/false)
            - is_clear: 问题是否清晰 (true/false)
            - ambiguities: 潜在歧义列表
            - missing_info: 缺失的关键信息列表
            - complexity: 问题复杂度 (simple/complex)
            
            严格要求：
            1. 仅返回JSON字符串，不包含任何解释、说明或其他文字
            2. 必须使用英文逗号分隔字段
            3. 布尔值使用小写的true/false
            4. 字符串必须使用双引号
            5. 数组元素使用双引号包裹
            6. 不要添加任何额外的JSON结构或注释
            
            输出示例：
            {{
                "is_complete": false, "is_clear": true,
                "ambiguities": ["是否需要考虑商业用途？"],
                "missing_info": ["各框架的最新版本是什么？"],
                "complexity": "complex"
            }}
            """

            response = self.generate_response(prompt)
            self.logger.debug(f"LLM原始响应: '{response}'")

            if not response.strip():
                self.logger.error("LLM返回了空响应")
                return {
                    "is_complete": True,
                    "is_clear": True,
                    "ambiguities": [],
                    "missing_info": [],
                    "complexity": "complex",
                }

            # 预处理响应
            response = response.strip()

            # 替换中文逗号为英文逗号
            response = response.replace("，", ",")

            # 移除可能的非JSON内容
            # 移除JSON前后的所有非JSON字符
            json_match = re.search(r"\{.*?\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # 如果没有找到完整JSON，尝试提取所有JSON片段
                json_parts = []
                brace_count = 0
                start_pos = None
                for i, char in enumerate(response):
                    if char == "{":
                        if brace_count == 0:
                            start_pos = i
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0 and start_pos is not None:
                            json_parts.append(response[start_pos : i + 1])
                            start_pos = None

                if json_parts:
                    # 选择最长的JSON片段（通常最完整）
                    json_str = max(json_parts, key=len)
                else:
                    json_str = response

            self.logger.debug(f"提取的JSON部分: '{json_str}'")

            # 尝试解析JSON
            try:
                result = json.loads(json_str)
                # 类型断言确保返回Dict[str, Any]类型
                return cast(Dict[str, Any], result)
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败，响应内容: '{response}'，错误: {e}")
                # 尝试更宽容的解析
                try:
                    # 修复常见的格式问题
                    # 1. 确保所有字符串用双引号包裹
                    json_str = re.sub(r"'([^']+)'", r'"\1"', json_str)
                    # 2. 移除尾部可能的逗号
                    json_str = re.sub(r",\s*([}\[\]])", r"\1", json_str)
                    # 3. 确保布尔值是小写
                    json_str = json_str.replace("True", "true").replace(
                        "False", "false"
                    )
                    # 4. 确保复杂度值是小写
                    json_str = json_str.replace("Simple", "simple").replace(
                        "Complex", "complex"
                    )

                    self.logger.debug(f"修复后的JSON: '{json_str}'")
                    result = json.loads(json_str)
                    # 类型断言确保返回Dict[str, Any]类型
                    return cast(Dict[str, Any], result)
                except json.JSONDecodeError:
                    self.logger.error("修复后仍解析失败")
                    return {
                        "is_complete": True,
                        "is_clear": True,
                        "ambiguities": [],
                        "missing_info": [],
                        "complexity": "complex",
                    }
        except Exception as e:
            self.logger.error(f"LLM分析问题失败: {e}")
            raise

    def generate_clarification_question(
        self, original_question: str, analysis: Dict[str, Any]
    ) -> str:
        """根据问题分析生成澄清问题"""
        try:
            prompt = f"""
            请根据以下问题分析结果，生成一个针对性的澄清问题：
            
            原始问题："{original_question}"
            
            问题分析：
            - 完整性：{"完整" if analysis["is_complete"] else "不完整"}
            - 清晰度：{"清晰" if analysis["is_clear"] else "不清晰"}
            - 潜在歧义：{
                ", ".join(analysis["ambiguities"]) if analysis["ambiguities"] else "无"
            }
            - 缺失信息：{
                ", ".join(analysis["missing_info"])
                if analysis["missing_info"]
                else "无"
            }
            - 复杂度：{analysis["complexity"]}
            
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
            你是专业的问题重构专家，请仅返回重构后的问题文本，不要添加任何其他内容。
            
            原始问题："{original_question}"
            
            澄清信息：
            {chr(10).join([f"- {clarification}" for clarification in clarifications])}
            
            严格要求：
            1. 绝对不要包含"重构后的问题："等任何前缀或标签
            2. 只返回一个最终的重构问题，不要返回多个变体
            3. 不包含任何思考过程、解释或说明
            4. 问题必须专业、完整、清晰无歧义
            5. 准确反映用户核心意图
            
            输出示例：
            请推荐三个用于开发AI Agent的主流框架，并详细比较它们的
            功能特性、适用场景及技术优势等方面的异同。
            """

            response = self.generate_response(prompt)
            # 清理响应，提取有效问题
            response = response.strip()

            # 移除所有可能的前缀，包括重复出现的前缀
            import re

            # 移除所有"重构后的问题："前缀（包括重复出现的）
            response = re.sub(r"重构后的问题：\s*", "", response)
            # 移除其他可能的前缀
            unwanted_prefixes = [
                r"最终问题：\s*",
                r"答案：\s*",
                r"结果：\s*",
                r"我将为您重构问题：\s*",
                r"根据您的要求：\s*",
            ]
            for prefix in unwanted_prefixes:
                response = re.sub(prefix, "", response)

            # 分割多个候选问题（如果有）
            candidate_questions = []
            # 匹配以问号结尾的句子
            question_matches = re.findall(r"([^?]+\?)", response, re.DOTALL)
            if question_matches:
                candidate_questions = [q.strip() for q in question_matches]
            else:
                # 如果没有问号，按换行或分号分割
                for sep in ["\n", ";", "；"]:
                    if sep in response:
                        candidate_questions = [
                            q.strip() for q in response.split(sep) if q.strip()
                        ]
                        break

            # 选择最相关的问题
            if candidate_questions:
                # 优先选择最长的问题（通常更完整）
                response = max(candidate_questions, key=len)

            # 最终清理
            response = response.strip()

            # 移除常见的思考过程短语
            unwanted_phrases = [
                "最后，我会再次检查",
                "确保没有遗漏",
                "最终呈现",
                "符合所有要求",
                "严格要求中的各项规定",
                "现在我需要根据",
                "我将按照要求",
                "首先，我需要",
                "接下来是",
                "现在要处理",
            ]

            for phrase in unwanted_phrases:
                if phrase in response:
                    # 如果包含思考过程，尝试提取有用的问题部分
                    import re

                    # 尝试找到以问号结尾的句子
                    question_matches = re.findall(r"([^?]+\?)", response, re.DOTALL)
                    if question_matches:
                        response = question_matches[-1].strip()
                    break

            # 确保返回有效问题
            # 检查是否是真正的问题（包含问号或关键疑问词）
            has_question_mark = "?" in response
            has_question_words = any(
                word in response
                for word in [
                    "如何",
                    "什么",
                    "哪个",
                    "是否",
                    "为什么",
                    "推荐",
                    "比较",
                    "分析",
                ]
            )

            if (
                not response
                or not (has_question_mark or has_question_words)
                or "重构问题" in response
                or "重构要求" in response
            ):
                return original_question

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

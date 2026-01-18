from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, cast

from src.infrastructure.data.data_manager import DataManager
from src.infrastructure.llm.llm_service import LLMService
from src.infrastructure.logging.logger import get_logger


@dataclass
class InteractionState:
    session_id: int
    original_question: str
    refined_question: Optional[str] = None
    clarification_rounds: int = 0
    clarifications: List[str] = field(default_factory=list)
    completed: bool = False

    def __post_init__(self) -> None:
        pass


class InteractionEngine:
    def __init__(
        self,
        llm_service: LLMService,
        data_manager: DataManager,
        max_clarification_rounds: int = 3,
    ):
        self.llm_service = llm_service
        self.data_manager = data_manager
        self.max_clarification_rounds = max_clarification_rounds
        self.logger = get_logger()

    def start_interaction(self, original_question: str) -> InteractionState:
        """开始新的交互会话"""
        # 保存会话到数据库
        session_id = self.data_manager.save_session(original_question)

        # 创建交互状态
        state = InteractionState(
            session_id=session_id, original_question=original_question
        )

        self.logger.info(f"开始新的交互会话，会话ID: {session_id}")

        return state

    def analyze_question(self, state: InteractionState) -> Dict[str, Any]:
        """分析问题"""
        try:
            analysis = self.llm_service.analyze_question(state.original_question)
            self.logger.info(f"问题分析结果: {analysis}")
            # 类型断言确保返回Dict[str, Any]类型
            return cast(Dict[str, Any], analysis)
        except Exception as e:
            self.logger.error(f"分析问题失败: {e}")
            raise

    def generate_clarification(
        self, state: InteractionState, analysis: Dict[str, Any]
    ) -> Optional[str]:
        """生成澄清问题"""
        if state.clarification_rounds >= self.max_clarification_rounds:
            self.logger.info(f"已达到最大澄清轮数 ({self.max_clarification_rounds})")
            return None

        # 检查是否需要澄清
        if (
            analysis["is_complete"]
            and analysis["is_clear"]
            and not analysis["ambiguities"]
        ):
            self.logger.info("问题已足够完整和清晰，无需澄清")
            return None

        try:
            clarification = self.llm_service.generate_clarification_question(
                state.original_question, analysis
            )
            state.clarification_rounds += 1

            self.logger.info(
                f"生成澄清问题 ({state.clarification_rounds}/"
                f"{self.max_clarification_rounds}): {clarification}"
            )

            # 类型断言确保返回Optional[str]类型
            return cast(Optional[str], clarification)
        except Exception as e:
            self.logger.error(f"生成澄清问题失败: {e}")
            raise

    def handle_clarification_response(
        self, state: InteractionState, response: str
    ) -> InteractionState:
        """处理用户的澄清响应"""
        state.clarifications.append(response)

        # 更新数据库中的会话记录
        self.data_manager.update_session(
            state.session_id, refined_question="\n".join(state.clarifications)
        )

        self.logger.info(f"收到澄清响应: {response}")

        return state

    def refine_question(self, state: InteractionState) -> str:
        """重构问题"""
        try:
            refined_question = self.llm_service.refine_question(
                state.original_question, state.clarifications
            )

            state.refined_question = refined_question

            # 更新数据库中的会话记录
            self.data_manager.update_session(
                state.session_id, refined_question=refined_question
            )

            self.logger.info(f"重构后的问题: {refined_question}")

            # 类型断言确保返回str类型
            return cast(str, refined_question)
        except Exception as e:
            self.logger.error(f"重构问题失败: {e}")
            raise

    def complete_interaction(self, state: InteractionState) -> InteractionState:
        """完成交互会话"""
        state.completed = True

        # 更新数据库中的会话记录
        self.data_manager.update_session(state.session_id, completed=True)

        self.logger.info(f"完成交互会话，会话ID: {state.session_id}")

        return state

    def get_session_state(self, session_id: int) -> Optional[InteractionState]:
        """从数据库获取会话状态"""
        session_record = self.data_manager.get_session(session_id)
        if not session_record:
            return None

        # 获取澄清信息
        tool_results = self.data_manager.get_tool_results(session_id)
        clarifications = []
        for result in tool_results:
            if result.tool_name == "clarification":
                clarifications.append(result.answer)

        return InteractionState(
            session_id=session_record.id,
            original_question=session_record.original_question,
            refined_question=session_record.refined_question,
            clarification_rounds=len(clarifications),
            clarifications=clarifications,
            completed=session_record.completed,
        )

    def is_clarification_needed(self, analysis: Dict[str, Any]) -> bool:
        """判断是否需要澄清"""
        return not (
            analysis["is_complete"]
            and analysis["is_clear"]
            and not analysis["ambiguities"]
        )

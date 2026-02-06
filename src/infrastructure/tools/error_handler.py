import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """错误类别"""

    NETWORK = "network"
    TOOL_EXECUTION = "tool_execution"
    LLM = "llm"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """错误信息"""

    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    recoverable: bool


class RecoveryStrategy:
    """恢复策略"""

    def __init__(
        self,
        name: str,
        can_recover: Callable[[ErrorInfo], bool],
        recover: Callable[[ErrorInfo], bool],
    ):
        self.name = name
        self.can_recover = can_recover
        self.recover = recover


class ErrorHandler:
    """错误处理器"""

    def __init__(self) -> None:
        self.error_history: List[ErrorInfo] = []
        self.recovery_strategies: List[RecoveryStrategy] = []
        self._register_default_strategies()

    def handle_error(self, error: Exception, context: Dict[str, Any]) -> ErrorInfo:
        """处理错误"""
        error_info = self._create_error_info(error, context)
        self.error_history.append(error_info)

        if error_info.recoverable:
            for strategy in self.recovery_strategies:
                if strategy.can_recover(error_info):
                    try:
                        if strategy.recover(error_info):
                            logger.info(f"使用策略 {strategy.name} 成功恢复")
                            break
                    except Exception as e:
                        logger.error(f"恢复策略 {strategy.name} 执行失败: {e}")

        return error_info

    def _create_error_info(
        self, error: Exception, context: Dict[str, Any]
    ) -> ErrorInfo:
        """创建错误信息"""
        category = self._classify_error(error)
        severity = self._determine_severity(error)
        recoverable = self._is_recoverable(error)

        return ErrorInfo(
            error_id=str(uuid.uuid4()),
            category=category,
            severity=severity,
            message=str(error),
            details=context,
            timestamp=datetime.now(),
            recoverable=recoverable,
        )

    def _classify_error(self, error: Exception) -> ErrorCategory:
        """分类错误"""
        error_type = type(error).__name__

        if "network" in error_type.lower() or "connection" in error_type.lower():
            return ErrorCategory.NETWORK
        elif "llm" in error_type.lower() or "model" in error_type.lower():
            return ErrorCategory.LLM
        elif "database" in error_type.lower() or "sqlite" in error_type.lower():
            return ErrorCategory.DATABASE
        elif "config" in error_type.lower() or "yaml" in error_type.lower():
            return ErrorCategory.CONFIGURATION
        elif "tool" in error_type.lower() or "execution" in error_type.lower():
            return ErrorCategory.TOOL_EXECUTION
        else:
            return ErrorCategory.UNKNOWN

    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """确定错误严重程度"""
        error_type = type(error).__name__
        error_message = str(error).lower()

        if "critical" in error_type.lower() or "fatal" in error_type.lower():
            return ErrorSeverity.CRITICAL
        elif "timeout" in error_type.lower() or "network" in error_type.lower():
            return ErrorSeverity.HIGH
        elif "database" in error_type.lower() or "corruption" in error_message:
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.MEDIUM

    def _is_recoverable(self, error: Exception) -> bool:
        """判断错误是否可恢复"""
        error_type = type(error).__name__
        error_message = str(error).lower()

        recoverable_keywords = ["timeout", "network", "connection", "temporary"]
        return any(
            keyword in error_type.lower() or keyword in error_message
            for keyword in recoverable_keywords
        )

    def _register_default_strategies(self) -> None:
        """注册默认恢复策略"""

        def can_retry_timeout(error: ErrorInfo) -> bool:
            return (
                error.category == ErrorCategory.NETWORK
                and "timeout" in error.message.lower()
            )

        def retry_timeout(error: ErrorInfo) -> bool:
            logger.info(f"尝试重试超时操作: {error.error_id}")
            return True

        self.recovery_strategies.append(
            RecoveryStrategy("retry_timeout", can_retry_timeout, retry_timeout)
        )

    def add_recovery_strategy(self, strategy: RecoveryStrategy) -> None:
        """添加恢复策略"""
        self.recovery_strategies.append(strategy)

    def remove_recovery_strategy(self, strategy_name: str) -> None:
        """移除恢复策略"""
        self.recovery_strategies = [
            s for s in self.recovery_strategies if s.name != strategy_name
        ]

    def get_error_history(self) -> List[ErrorInfo]:
        """获取错误历史"""
        return self.error_history.copy()

    def clear_error_history(self) -> None:
        """清空错误历史"""
        self.error_history.clear()

    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorInfo]:
        """按类别获取错误"""
        return [e for e in self.error_history if e.category == category]

    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorInfo]:
        """按严重程度获取错误"""
        return [e for e in self.error_history if e.severity == severity]

from datetime import datetime

from src.infrastructure.tools.error_handler import (
    ErrorCategory,
    ErrorHandler,
    ErrorInfo,
    ErrorSeverity,
    RecoveryStrategy,
)


class TestErrorSeverity:
    """测试ErrorSeverity枚举"""

    def test_severity_values(self) -> None:
        """测试严重程度值"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestErrorCategory:
    """测试ErrorCategory枚举"""

    def test_category_values(self) -> None:
        """测试类别值"""
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.TOOL_EXECUTION.value == "tool_execution"
        assert ErrorCategory.LLM.value == "llm"
        assert ErrorCategory.DATABASE.value == "database"
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestErrorInfo:
    """测试ErrorInfo数据类"""

    def test_error_info_creation(self) -> None:
        """测试创建错误信息"""
        error_info = ErrorInfo(
            error_id="test-id",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            message="测试错误",
            details={"context": "test"},
            timestamp=datetime.now(),
            recoverable=True,
        )

        assert error_info.error_id == "test-id"
        assert error_info.category == ErrorCategory.NETWORK
        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.message == "测试错误"
        assert error_info.recoverable is True


class TestRecoveryStrategy:
    """测试RecoveryStrategy类"""

    def test_recovery_strategy_creation(self) -> None:
        """测试创建恢复策略"""

        def can_recover(error: ErrorInfo) -> bool:
            return error.recoverable

        def recover(error: ErrorInfo) -> bool:
            return True

        strategy = RecoveryStrategy("test_strategy", can_recover, recover)

        assert strategy.name == "test_strategy"
        assert strategy.can_recover is not None
        assert strategy.recover is not None


class TestErrorHandler:
    """测试ErrorHandler类"""

    def test_init(self) -> None:
        """测试初始化"""
        handler = ErrorHandler()
        assert handler.error_history == []
        assert len(handler.recovery_strategies) > 0

    def test_handle_error(self) -> None:
        """测试处理错误"""
        handler = ErrorHandler()

        error = Exception("测试错误")
        context = {"test": "context"}

        error_info = handler.handle_error(error, context)

        assert error_info.message == "测试错误"
        assert len(handler.error_history) == 1

    def test_classify_error_network(self) -> None:
        """测试分类错误（网络）"""
        handler = ErrorHandler()

        class NetworkError(Exception):
            pass

        error = NetworkError("网络连接失败")
        category = handler._classify_error(error)

        assert category == ErrorCategory.NETWORK

    def test_classify_error_llm(self) -> None:
        """测试分类错误（LLM）"""
        handler = ErrorHandler()

        class LLMError(Exception):
            pass

        error = LLMError("模型加载失败")
        category = handler._classify_error(error)

        assert category == ErrorCategory.LLM

    def test_classify_error_database(self) -> None:
        """测试分类错误（数据库）"""
        handler = ErrorHandler()

        class DatabaseError(Exception):
            pass

        error = DatabaseError("数据库连接失败")
        category = handler._classify_error(error)

        assert category == ErrorCategory.DATABASE

    def test_classify_error_configuration(self) -> None:
        """测试分类错误（配置）"""
        handler = ErrorHandler()

        class ConfigError(Exception):
            pass

        error = ConfigError("配置文件解析失败")
        category = handler._classify_error(error)

        assert category == ErrorCategory.CONFIGURATION

    def test_determine_severity_critical(self) -> None:
        """测试确定错误严重程度（严重）"""
        handler = ErrorHandler()

        class CriticalError(Exception):
            pass

        error = CriticalError("严重错误")
        severity = handler._determine_severity(error)

        assert severity == ErrorSeverity.CRITICAL

    def test_determine_severity_timeout(self) -> None:
        """测试确定错误严重程度（超时）"""
        handler = ErrorHandler()

        class TimeoutError(Exception):
            pass

        error = TimeoutError("请求超时")
        severity = handler._determine_severity(error)

        assert severity == ErrorSeverity.HIGH

    def test_determine_severity_medium(self) -> None:
        """测试确定错误严重程度（中等）"""
        handler = ErrorHandler()

        error = Exception("普通错误")
        severity = handler._determine_severity(error)

        assert severity == ErrorSeverity.MEDIUM

    def test_is_recoverable(self) -> None:
        """测试判断错误是否可恢复"""
        handler = ErrorHandler()

        class TimeoutError(Exception):
            pass

        error = TimeoutError("请求超时")
        recoverable = handler._is_recoverable(error)

        assert recoverable is True

    def test_is_not_recoverable(self) -> None:
        """测试判断错误是否不可恢复"""
        handler = ErrorHandler()

        error = Exception("不可恢复的错误")
        recoverable = handler._is_recoverable(error)

        assert recoverable is False

    def test_add_recovery_strategy(self) -> None:
        """测试添加恢复策略"""
        handler = ErrorHandler()

        def can_recover(error: ErrorInfo) -> bool:
            return True

        def recover(error: ErrorInfo) -> bool:
            return True

        strategy = RecoveryStrategy("test", can_recover, recover)
        initial_count = len(handler.recovery_strategies)

        handler.add_recovery_strategy(strategy)

        assert len(handler.recovery_strategies) == initial_count + 1

    def test_remove_recovery_strategy(self) -> None:
        """测试移除恢复策略"""
        handler = ErrorHandler()

        def can_recover(error: ErrorInfo) -> bool:
            return True

        def recover(error: ErrorInfo) -> bool:
            return True

        strategy = RecoveryStrategy("test_remove", can_recover, recover)
        handler.add_recovery_strategy(strategy)

        handler.remove_recovery_strategy("test_remove")

        assert not any(s.name == "test_remove" for s in handler.recovery_strategies)

    def test_get_error_history(self) -> None:
        """测试获取错误历史"""
        handler = ErrorHandler()

        error = Exception("测试错误")
        handler.handle_error(error, {})

        history = handler.get_error_history()

        assert len(history) == 1
        assert history[0].message == "测试错误"

    def test_clear_error_history(self) -> None:
        """测试清空错误历史"""
        handler = ErrorHandler()

        error = Exception("测试错误")
        handler.handle_error(error, {})

        handler.clear_error_history()

        assert len(handler.error_history) == 0

    def test_get_errors_by_category(self) -> None:
        """测试按类别获取错误"""
        handler = ErrorHandler()

        class NetworkError(Exception):
            pass

        class DatabaseError(Exception):
            pass

        handler.handle_error(NetworkError("网络错误"), {})
        handler.handle_error(DatabaseError("数据库错误"), {})

        network_errors = handler.get_errors_by_category(ErrorCategory.NETWORK)

        assert len(network_errors) == 1
        assert network_errors[0].category == ErrorCategory.NETWORK

    def test_get_errors_by_severity(self) -> None:
        """测试按严重程度获取错误"""
        handler = ErrorHandler()

        class TimeoutError(Exception):
            pass

        class NormalError(Exception):
            pass

        handler.handle_error(TimeoutError("超时错误"), {})
        handler.handle_error(NormalError("普通错误"), {})

        high_severity_errors = handler.get_errors_by_severity(ErrorSeverity.HIGH)

        assert len(high_severity_errors) == 1
        assert high_severity_errors[0].severity == ErrorSeverity.HIGH

    def test_multiple_errors(self) -> None:
        """测试处理多个错误"""
        handler = ErrorHandler()

        for i in range(5):
            error = Exception(f"错误{i}")
            handler.handle_error(error, {"index": i})

        assert len(handler.error_history) == 5

    def test_recovery_strategy_execution(self) -> None:
        """测试恢复策略执行"""
        handler = ErrorHandler()

        recovery_called = []

        def can_recover(error: ErrorInfo) -> bool:
            return error.recoverable

        def recover(error: ErrorInfo) -> bool:
            recovery_called.append(True)
            return True

        strategy = RecoveryStrategy("test_recovery", can_recover, recover)
        handler.add_recovery_strategy(strategy)

        class TimeoutError(Exception):
            pass

        error = TimeoutError("请求超时")
        handler.handle_error(error, {})

        assert len(recovery_called) > 0

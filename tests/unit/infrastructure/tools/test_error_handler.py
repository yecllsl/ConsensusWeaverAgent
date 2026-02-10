"""测试错误处理器"""

from src.infrastructure.tools.error_handler import (
    ErrorCategory,
    ErrorInfo,
    ErrorSeverity,
    RecoveryStrategy,
)


class TestErrorSeverity:
    """测试错误严重程度"""

    def test_low_severity(self):
        """测试低严重程度"""
        assert ErrorSeverity.LOW.value == "low"

    def test_medium_severity(self):
        """测试中等严重程度"""
        assert ErrorSeverity.MEDIUM.value == "medium"

    def test_high_severity(self):
        """测试高严重程度"""
        assert ErrorSeverity.HIGH.value == "high"

    def test_critical_severity(self):
        """测试严重程度"""
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestErrorCategory:
    """测试错误类别"""

    def test_network_category(self):
        """测试网络错误类别"""
        assert ErrorCategory.NETWORK.value == "network"

    def test_tool_execution_category(self):
        """测试工具执行错误类别"""
        assert ErrorCategory.TOOL_EXECUTION.value == "tool_execution"

    def test_llm_category(self):
        """测试LLM错误类别"""
        assert ErrorCategory.LLM.value == "llm"

    def test_database_category(self):
        """测试数据库错误类别"""
        assert ErrorCategory.DATABASE.value == "database"

    def test_configuration_category(self):
        """测试配置错误类别"""
        assert ErrorCategory.CONFIGURATION.value == "configuration"

    def test_unknown_category(self):
        """测试未知错误类别"""
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestRecoveryStrategy:
    """测试恢复策略"""

    def test_init(self):
        """测试初始化"""
        strategy = RecoveryStrategy(
            name="test_strategy",
            can_recover=lambda error: True,
            recover=lambda error: None,
        )

        assert strategy.name == "test_strategy"

    def test_can_recover(self):
        """测试是否可以恢复"""
        strategy = RecoveryStrategy(
            name="test_strategy",
            can_recover=lambda error: error.severity != ErrorSeverity.CRITICAL,
            recover=lambda error: None,
        )

        error = ErrorInfo(
            error_id="1",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.LOW,
            message="测试错误",
            details={},
            timestamp=None,
            recoverable=True,
        )

        assert strategy.can_recover(error) is True

    def test_cannot_recover(self):
        """测试是否不能恢复"""
        strategy = RecoveryStrategy(
            name="test_strategy",
            can_recover=lambda error: error.severity != ErrorSeverity.CRITICAL,
            recover=lambda error: None,
        )

        error = ErrorInfo(
            error_id="1",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.CRITICAL,
            message="测试错误",
            details={},
            timestamp=None,
            recoverable=False,
        )

        assert strategy.can_recover(error) is False

    def test_recover(self):
        """测试恢复"""
        recovered = [False]

        def recover_func(error):
            recovered[0] = True

        strategy = RecoveryStrategy(
            name="test_strategy",
            can_recover=lambda error: True,
            recover=recover_func,
        )

        error = ErrorInfo(
            error_id="1",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.LOW,
            message="测试错误",
            details={},
            timestamp=None,
            recoverable=True,
        )

        strategy.recover(error)
        assert recovered[0] is True

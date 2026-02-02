import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.monitoring.performance_monitor import (
    PerformanceAlert,
    PerformanceMetric,
    PerformanceMonitor,
    PerformanceReport,
    PerformanceThresholds,
)


@pytest.fixture
def performance_monitor():
    """创建性能监控器实例"""
    monitor = PerformanceMonitor()
    monitor.metrics = []
    monitor.alerts = []
    monitor.current_session_metrics = []
    return monitor


class TestPerformanceMonitor:
    """测试性能监控器"""

    def test_init(self, performance_monitor):
        """测试初始化"""
        assert performance_monitor.thresholds is not None
        assert isinstance(performance_monitor.metrics, list)
        assert isinstance(performance_monitor.alerts, list)
        assert performance_monitor.current_session_start > 0

    def test_init_with_custom_thresholds(self):
        """测试使用自定义阈值初始化"""
        thresholds = PerformanceThresholds(
            max_response_time=5.0,
            max_memory_usage_mb=512.0,
            max_cpu_usage_percent=70.0,
        )
        monitor = PerformanceMonitor(thresholds)

        assert monitor.thresholds.max_response_time == 5.0
        assert monitor.thresholds.max_memory_usage_mb == 512.0
        assert monitor.thresholds.max_cpu_usage_percent == 70.0

    def test_record_metric(self, performance_monitor):
        """测试记录性能指标"""
        performance_monitor.record_metric(1.5)

        assert len(performance_monitor.metrics) == 1
        assert len(performance_monitor.current_session_metrics) == 1
        assert performance_monitor.metrics[0].response_time == 1.5

    def test_record_metric_multiple(self, performance_monitor):
        """测试记录多个性能指标"""
        performance_monitor.record_metric(1.0)
        performance_monitor.record_metric(2.0)
        performance_monitor.record_metric(3.0)

        assert len(performance_monitor.metrics) == 3
        assert len(performance_monitor.current_session_metrics) == 3

    def test_record_metric_alert_response_time(self):
        """测试记录性能指标（响应时间告警）"""
        thresholds = PerformanceThresholds(
            max_response_time=1.0,
            max_memory_usage_mb=999999,
        )
        monitor = PerformanceMonitor(thresholds)
        monitor.alerts = []

        monitor.record_metric(2.0)

        assert len(monitor.alerts) == 1
        assert monitor.alerts[0].alert_type == "response_time"
        assert monitor.alerts[0].severity == "warning"

    def test_record_metric_alert_memory_usage(self):
        """测试记录性能指标（内存使用告警）"""
        thresholds = PerformanceThresholds(max_memory_usage_mb=1.0)
        monitor = PerformanceMonitor(thresholds)

        with patch("psutil.virtual_memory") as mock_memory:
            mock_memory.return_value = MagicMock(used=2 * 1024 * 1024)
            monitor.record_metric(1.0)

        assert len(monitor.alerts) > 0
        memory_alerts = [a for a in monitor.alerts if a.alert_type == "memory_usage"]
        assert len(memory_alerts) > 0

    def test_get_realtime_metrics(self, performance_monitor):
        """测试获取实时性能指标"""
        metrics = performance_monitor.get_realtime_metrics()

        assert "memory_usage_mb" in metrics
        assert "cpu_usage_percent" in metrics
        assert "disk_io_read_mb" in metrics
        assert "disk_io_write_mb" in metrics
        assert "network_sent_mb" in metrics
        assert "network_recv_mb" in metrics

    def test_generate_report_empty(self, performance_monitor):
        """测试生成性能报告（空）"""
        report = performance_monitor.generate_report()

        assert isinstance(report, PerformanceReport)
        assert report.total_requests == 0
        assert report.average_response_time == 0.0

    def test_generate_report_with_metrics(self, performance_monitor):
        """测试生成性能报告（有指标）"""
        performance_monitor.record_metric(1.0)
        performance_monitor.record_metric(2.0)
        performance_monitor.record_metric(3.0)

        report = performance_monitor.generate_report()

        assert isinstance(report, PerformanceReport)
        assert report.total_requests == 3
        assert report.average_response_time == 2.0
        assert report.min_response_time == 1.0
        assert report.max_response_time == 3.0

    def test_get_performance_trend_empty(self, performance_monitor):
        """测试获取性能趋势（空）"""
        trend = performance_monitor.get_performance_trend(hours=24)

        assert "response_times" in trend
        assert "memory_usages" in trend
        assert "cpu_usages" in trend
        assert len(trend["response_times"]) == 0

    def test_get_performance_trend_with_metrics(self, performance_monitor):
        """测试获取性能趋势（有指标）"""
        performance_monitor.record_metric(1.0)
        performance_monitor.record_metric(2.0)

        trend = performance_monitor.get_performance_trend(hours=24)

        assert len(trend["response_times"]) == 2
        assert len(trend["memory_usages"]) == 2
        assert len(trend["cpu_usages"]) == 2

    def test_reset_session(self, performance_monitor):
        """测试重置会话"""
        performance_monitor.record_metric(1.0)
        performance_monitor.record_metric(2.0)

        performance_monitor.reset_session()

        assert len(performance_monitor.current_session_metrics) == 0
        assert len(performance_monitor.metrics) == 2

    def test_clear_all_metrics(self, performance_monitor):
        """测试清除所有指标"""
        performance_monitor.record_metric(1.0)
        performance_monitor.record_metric(2.0)

        performance_monitor.clear_all_metrics()

        assert len(performance_monitor.metrics) == 0
        assert len(performance_monitor.alerts) == 0
        assert len(performance_monitor.current_session_metrics) == 0

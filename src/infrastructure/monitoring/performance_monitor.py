import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import psutil

from src.infrastructure.logging.logger import get_logger


@dataclass
class PerformanceMetric:
    """性能指标"""

    timestamp: str
    response_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float


@dataclass
class PerformanceAlert:
    """性能告警"""

    alert_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: str
    metric_value: float
    threshold: float


@dataclass
class PerformanceReport:
    """性能报告"""

    report_id: str
    start_time: str
    end_time: str
    duration_seconds: float
    total_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    average_memory_usage_mb: float
    average_cpu_usage_percent: float
    metrics: List[PerformanceMetric]
    alerts: List[PerformanceAlert]


@dataclass
class PerformanceThresholds:
    """性能阈值"""

    max_response_time: float = 10.0
    max_memory_usage_mb: float = 1024.0
    max_cpu_usage_percent: float = 80.0
    max_disk_io_mb: float = 100.0
    max_network_io_mb: float = 100.0


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, thresholds: Optional[PerformanceThresholds] = None):
        self.thresholds = thresholds or PerformanceThresholds()
        self.logger = get_logger()
        self.metrics_file = "data/performance_metrics.json"
        self.alerts_file = "data/performance_alerts.json"
        self.metrics: List[PerformanceMetric] = []
        self.alerts: List[PerformanceAlert] = []
        self.current_session_start = time.time()
        self.current_session_metrics: List[PerformanceMetric] = []
        self._load_metrics()
        self._load_alerts()

        # 记录初始系统状态
        self.initial_disk_io = psutil.disk_io_counters()
        self.initial_network_io = psutil.net_io_counters()

        self.logger.info("性能监控器初始化完成")

    def _load_metrics(self) -> None:
        """加载历史性能指标"""
        if not os.path.exists(self.metrics_file):
            self.logger.info("性能指标文件不存在，创建空指标")
            return

        try:
            with open(self.metrics_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for metric_data in data:
                self.metrics.append(
                    PerformanceMetric(
                        timestamp=metric_data["timestamp"],
                        response_time=metric_data["response_time"],
                        memory_usage_mb=metric_data["memory_usage_mb"],
                        cpu_usage_percent=metric_data["cpu_usage_percent"],
                        disk_io_read_mb=metric_data["disk_io_read_mb"],
                        disk_io_write_mb=metric_data["disk_io_write_mb"],
                        network_sent_mb=metric_data["network_sent_mb"],
                        network_recv_mb=metric_data["network_recv_mb"],
                    )
                )

            self.logger.info(f"已加载 {len(self.metrics)} 条历史性能指标")

        except Exception as e:
            self.logger.error(f"加载性能指标失败: {e}")

    def _save_metrics(self) -> None:
        """保存性能指标"""
        try:
            data = []
            for metric in self.metrics:
                data.append(
                    {
                        "timestamp": metric.timestamp,
                        "response_time": metric.response_time,
                        "memory_usage_mb": metric.memory_usage_mb,
                        "cpu_usage_percent": metric.cpu_usage_percent,
                        "disk_io_read_mb": metric.disk_io_read_mb,
                        "disk_io_write_mb": metric.disk_io_write_mb,
                        "network_sent_mb": metric.network_sent_mb,
                        "network_recv_mb": metric.network_recv_mb,
                    }
                )

            os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
            with open(self.metrics_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info("性能指标已保存")

        except Exception as e:
            self.logger.error(f"保存性能指标失败: {e}")

    def _load_alerts(self) -> None:
        """加载历史告警"""
        if not os.path.exists(self.alerts_file):
            self.logger.info("性能告警文件不存在，创建空告警")
            return

        try:
            with open(self.alerts_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for alert_data in data:
                self.alerts.append(
                    PerformanceAlert(
                        alert_id=alert_data["alert_id"],
                        alert_type=alert_data["alert_type"],
                        severity=alert_data["severity"],
                        message=alert_data["message"],
                        timestamp=alert_data["timestamp"],
                        metric_value=alert_data["metric_value"],
                        threshold=alert_data["threshold"],
                    )
                )

            self.logger.info(f"已加载 {len(self.alerts)} 条历史告警")

        except Exception as e:
            self.logger.error(f"加载性能告警失败: {e}")

    def _save_alerts(self) -> None:
        """保存性能告警"""
        try:
            data = []
            for alert in self.alerts:
                data.append(
                    {
                        "alert_id": alert.alert_id,
                        "alert_type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "timestamp": alert.timestamp,
                        "metric_value": alert.metric_value,
                        "threshold": alert.threshold,
                    }
                )

            os.makedirs(os.path.dirname(self.alerts_file), exist_ok=True)
            with open(self.alerts_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info("性能告警已保存")

        except Exception as e:
            self.logger.error(f"保存性能告警失败: {e}")

    def _get_current_metrics(self) -> Dict[str, float]:
        """获取当前系统指标"""
        # 内存使用
        memory_info = psutil.virtual_memory()
        memory_usage_mb = memory_info.used / (1024 * 1024)

        # CPU使用率
        cpu_usage_percent = psutil.cpu_percent(interval=0.1)

        # 磁盘I/O
        disk_io = psutil.disk_io_counters()
        disk_io_read_mb = 0.0
        disk_io_write_mb = 0.0
        if disk_io and self.initial_disk_io:
            disk_io_read_mb = (disk_io.read_bytes - self.initial_disk_io.read_bytes) / (
                1024 * 1024
            )
            disk_io_write_mb = (
                disk_io.write_bytes - self.initial_disk_io.write_bytes
            ) / (1024 * 1024)

        # 网络I/O
        network_io = psutil.net_io_counters()
        network_sent_mb = 0.0
        network_recv_mb = 0.0
        if network_io and self.initial_network_io:
            network_sent_mb = (
                network_io.bytes_sent - self.initial_network_io.bytes_sent
            ) / (1024 * 1024)
            network_recv_mb = (
                network_io.bytes_recv - self.initial_network_io.bytes_recv
            ) / (1024 * 1024)

        return {
            "memory_usage_mb": memory_usage_mb,
            "cpu_usage_percent": cpu_usage_percent,
            "disk_io_read_mb": disk_io_read_mb,
            "disk_io_write_mb": disk_io_write_mb,
            "network_sent_mb": network_sent_mb,
            "network_recv_mb": network_recv_mb,
        }

    def record_metric(self, response_time: float) -> None:
        """记录性能指标"""
        current_metrics = self._get_current_metrics()

        metric = PerformanceMetric(
            timestamp=datetime.now().isoformat(),
            response_time=response_time,
            memory_usage_mb=current_metrics["memory_usage_mb"],
            cpu_usage_percent=current_metrics["cpu_usage_percent"],
            disk_io_read_mb=current_metrics["disk_io_read_mb"],
            disk_io_write_mb=current_metrics["disk_io_write_mb"],
            network_sent_mb=current_metrics["network_sent_mb"],
            network_recv_mb=current_metrics["network_recv_mb"],
        )

        self.metrics.append(metric)
        self.current_session_metrics.append(metric)

        # 检查告警
        self._check_alerts(metric)

        self.logger.info(
            f"记录性能指标: 响应时间={response_time:.2f}秒, "
            f"内存={metric.memory_usage_mb:.2f}MB, "
            f"CPU={metric.cpu_usage_percent:.1f}%"
        )

        # 定期保存
        if len(self.metrics) % 10 == 0:
            self._save_metrics()

    def _check_alerts(self, metric: PerformanceMetric) -> None:
        """检查性能告警"""
        alerts = []

        # 响应时间告警
        if metric.response_time > self.thresholds.max_response_time:
            alerts.append(
                PerformanceAlert(
                    alert_id=f"response_time_{int(time.time())}",
                    alert_type="response_time",
                    severity="warning",
                    message="响应时间超过阈值",
                    timestamp=metric.timestamp,
                    metric_value=metric.response_time,
                    threshold=self.thresholds.max_response_time,
                )
            )

        # 内存使用告警
        if metric.memory_usage_mb > self.thresholds.max_memory_usage_mb:
            alerts.append(
                PerformanceAlert(
                    alert_id=f"memory_usage_{int(time.time())}",
                    alert_type="memory_usage",
                    severity="warning",
                    message="内存使用超过阈值",
                    timestamp=metric.timestamp,
                    metric_value=metric.memory_usage_mb,
                    threshold=self.thresholds.max_memory_usage_mb,
                )
            )

        # CPU使用率告警
        if metric.cpu_usage_percent > self.thresholds.max_cpu_usage_percent:
            alerts.append(
                PerformanceAlert(
                    alert_id=f"cpu_usage_{int(time.time())}",
                    alert_type="cpu_usage",
                    severity="warning",
                    message="CPU使用率超过阈值",
                    timestamp=metric.timestamp,
                    metric_value=metric.cpu_usage_percent,
                    threshold=self.thresholds.max_cpu_usage_percent,
                )
            )

        # 磁盘I/O告警
        total_disk_io = metric.disk_io_read_mb + metric.disk_io_write_mb
        if total_disk_io > self.thresholds.max_disk_io_mb:
            alerts.append(
                PerformanceAlert(
                    alert_id=f"disk_io_{int(time.time())}",
                    alert_type="disk_io",
                    severity="info",
                    message="磁盘I/O超过阈值",
                    timestamp=metric.timestamp,
                    metric_value=total_disk_io,
                    threshold=self.thresholds.max_disk_io_mb,
                )
            )

        # 网络I/O告警
        total_network_io = metric.network_sent_mb + metric.network_recv_mb
        if total_network_io > self.thresholds.max_network_io_mb:
            alerts.append(
                PerformanceAlert(
                    alert_id=f"network_io_{int(time.time())}",
                    alert_type="network_io",
                    severity="info",
                    message="网络I/O超过阈值",
                    timestamp=metric.timestamp,
                    metric_value=total_network_io,
                    threshold=self.thresholds.max_network_io_mb,
                )
            )

        # 添加告警
        for alert in alerts:
            self.alerts.append(alert)
            self.logger.warning(
                f"性能告警: {alert.alert_type} = {alert.metric_value:.2f}, "
                f"阈值 = {alert.threshold:.2f}"
            )

        if alerts:
            self._save_alerts()

    def generate_report(self) -> PerformanceReport:
        """生成性能报告"""
        if not self.current_session_metrics:
            self.logger.warning("当前会话没有性能指标")
            return PerformanceReport(
                report_id=f"report_{int(time.time())}",
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat(),
                duration_seconds=0.0,
                total_requests=0,
                average_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                average_memory_usage_mb=0.0,
                average_cpu_usage_percent=0.0,
                metrics=[],
                alerts=[],
            )

        start_time = self.current_session_metrics[0].timestamp
        end_time = self.current_session_metrics[-1].timestamp
        duration_seconds = time.time() - self.current_session_start

        response_times = [m.response_time for m in self.current_session_metrics]
        average_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)

        memory_usages = [m.memory_usage_mb for m in self.current_session_metrics]
        average_memory_usage_mb = sum(memory_usages) / len(memory_usages)

        cpu_usages = [m.cpu_usage_percent for m in self.current_session_metrics]
        average_cpu_usage_percent = sum(cpu_usages) / len(cpu_usages)

        # 获取当前会话的告警
        session_start = datetime.fromisoformat(start_time)
        session_alerts = [
            alert
            for alert in self.alerts
            if datetime.fromisoformat(alert.timestamp) >= session_start
        ]

        report = PerformanceReport(
            report_id=f"report_{int(time.time())}",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            total_requests=len(self.current_session_metrics),
            average_response_time=average_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            average_memory_usage_mb=average_memory_usage_mb,
            average_cpu_usage_percent=average_cpu_usage_percent,
            metrics=self.current_session_metrics.copy(),
            alerts=session_alerts,
        )

        self.logger.info(
            f"生成性能报告: 总请求数={report.total_requests}, "
            f"平均响应时间={report.average_response_time:.2f}秒"
        )

        return report

    def get_realtime_metrics(self) -> Dict[str, float]:
        """获取实时性能指标"""
        return self._get_current_metrics()

    def get_performance_trend(self, hours: int = 24) -> Dict[str, List[float]]:
        """获取性能趋势"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)

        recent_metrics = [
            metric
            for metric in self.metrics
            if datetime.fromisoformat(metric.timestamp).timestamp() >= cutoff_time
        ]

        if not recent_metrics:
            return {
                "response_times": [],
                "memory_usages": [],
                "cpu_usages": [],
            }

        return {
            "response_times": [m.response_time for m in recent_metrics],
            "memory_usages": [m.memory_usage_mb for m in recent_metrics],
            "cpu_usages": [m.cpu_usage_percent for m in recent_metrics],
        }

    def reset_session(self) -> None:
        """重置当前会话"""
        self.current_session_start = time.time()
        self.current_session_metrics.clear()
        self.logger.info("已重置当前会话")

    def clear_all_metrics(self) -> None:
        """清除所有性能指标"""
        self.metrics.clear()
        self.alerts.clear()
        self.current_session_metrics.clear()
        self.current_session_start = time.time()
        self._save_metrics()
        self._save_alerts()
        self.logger.info("已清除所有性能指标")

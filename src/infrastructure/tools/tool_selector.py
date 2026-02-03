import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.logging.logger import get_logger


@dataclass
class ToolPerformanceMetrics:
    """工具性能指标"""

    tool_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    success_rate: float = 0.0
    last_used: Optional[str] = None


@dataclass
class ToolRecommendation:
    """工具推荐"""

    tool_name: str
    score: float
    reason: str
    metrics: ToolPerformanceMetrics


@dataclass
class ToolUsageStats:
    """工具使用统计"""

    tool_name: str
    usage_count: int
    success_rate: float
    avg_execution_time: float
    last_used: Optional[str]


class ToolSelector:
    """智能工具选择器"""

    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.get_config()
        self.logger = get_logger()
        self.metrics_file = "data/tool_metrics.json"
        self.metrics: Dict[str, ToolPerformanceMetrics] = {}
        self._load_metrics()

        # 问题类型关键词映射
        self.question_type_keywords = {
            "code": [
                "代码",
                "编程",
                "函数",
                "类",
                "算法",
                "bug",
                "调试",
                "code",
                "programming",
                "function",
                "class",
                "algorithm",
                "debug",
            ],
            "general": [
                "问题",
                "解释",
                "说明",
                "什么是",
                "how",
                "what",
                "explain",
                "question",
            ],
            "analysis": [
                "分析",
                "比较",
                "对比",
                "总结",
                "analyze",
                "compare",
                "summary",
            ],
        }

        # 工具类型映射
        self.tool_type_mapping = {
            "iflow": ["general", "analysis"],
            "codebuddy": ["code"],
        }

        self.logger.info("智能工具选择器初始化完成")

    def _load_metrics(self) -> None:
        """加载工具性能指标"""
        if not os.path.exists(self.metrics_file):
            self.logger.info("工具性能指标文件不存在，创建默认指标")
            return

        try:
            with open(self.metrics_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for tool_name, metrics_data in data.items():
                self.metrics[tool_name] = ToolPerformanceMetrics(
                    tool_name=tool_name,
                    total_calls=metrics_data.get("total_calls", 0),
                    successful_calls=metrics_data.get("successful_calls", 0),
                    failed_calls=metrics_data.get("failed_calls", 0),
                    total_execution_time=metrics_data.get("total_execution_time", 0.0),
                    average_execution_time=metrics_data.get(
                        "average_execution_time", 0.0
                    ),
                    success_rate=metrics_data.get("success_rate", 0.0),
                    last_used=metrics_data.get("last_used"),
                )

            self.logger.info(f"已加载 {len(self.metrics)} 个工具的性能指标")

        except Exception as e:
            self.logger.error(f"加载工具性能指标失败: {e}")

    def _save_metrics(self) -> None:
        """保存工具性能指标"""
        try:
            data = {}
            for tool_name, metrics in self.metrics.items():
                data[tool_name] = {
                    "total_calls": metrics.total_calls,
                    "successful_calls": metrics.successful_calls,
                    "failed_calls": metrics.failed_calls,
                    "total_execution_time": metrics.total_execution_time,
                    "average_execution_time": metrics.average_execution_time,
                    "success_rate": metrics.success_rate,
                    "last_used": metrics.last_used,
                }

            os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
            with open(self.metrics_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info("工具性能指标已保存")

        except Exception as e:
            self.logger.error(f"保存工具性能指标失败: {e}")

    def _detect_question_type(self, question: str) -> str:
        """检测问题类型"""
        question_lower = question.lower()

        for question_type, keywords in self.question_type_keywords.items():
            for keyword in keywords:
                if keyword.lower() in question_lower:
                    return question_type

        return "general"

    def _calculate_tool_score(self, tool_name: str, question_type: str) -> float:
        """计算工具分数
        根据工具类型匹配度和性能指标计算一个分数
        """
        score = 0.0

        # 基础分：工具类型匹配
        if tool_name in self.tool_type_mapping:
            if question_type in self.tool_type_mapping[tool_name]:
                score += 0.5

        # 性能分：成功率
        if tool_name in self.metrics:
            metrics = self.metrics[tool_name]
            score += metrics.success_rate * 0.3

            # 性能分：执行时间（越短越好）
            if metrics.average_execution_time > 0:
                time_score = 1.0 / (1.0 + metrics.average_execution_time / 10.0)
                score += time_score * 0.2

        return min(score, 1.0)

    def select_tools(
        self, question: str, max_tools: int = 3
    ) -> List[ToolRecommendation]:
        """根据问题选择最适合的工具"""
        question_type = self._detect_question_type(question)

        self.logger.info(f"检测到问题类型: {question_type}, 开始选择工具")

        enabled_tools = [tool for tool in self.config.external_tools if tool.enabled]

        recommendations = []

        for tool in enabled_tools:
            score = self._calculate_tool_score(tool.name, question_type)
            metrics = self.metrics.get(
                tool.name,
                ToolPerformanceMetrics(tool_name=tool.name),
            )

            reason = self._generate_recommendation_reason(
                tool.name, question_type, score, metrics
            )

            recommendations.append(
                ToolRecommendation(
                    tool_name=tool.name,
                    score=score,
                    reason=reason,
                    metrics=metrics,
                )
            )

        # 按分数排序
        recommendations.sort(key=lambda x: x.score, reverse=True)

        # 返回前N个推荐
        selected = recommendations[:max_tools]

        self.logger.info(
            f"已选择 {len(selected)} 个工具: {[r.tool_name for r in selected]}"
        )

        return selected

    def _generate_recommendation_reason(
        self,
        tool_name: str,
        question_type: str,
        score: float,
        metrics: ToolPerformanceMetrics,
    ) -> str:
        """生成推荐原因"""
        reasons = []

        # 类型匹配
        if tool_name in self.tool_type_mapping:
            if question_type in self.tool_type_mapping[tool_name]:
                reasons.append("工具类型与问题类型匹配")

        # 性能指标
        if metrics.total_calls > 0:
            if metrics.success_rate >= 0.8:
                reasons.append(f"成功率高 ({metrics.success_rate:.1%})")
            if metrics.average_execution_time < 5.0:
                reasons.append(f"执行速度快 ({metrics.average_execution_time:.2f}秒)")

        if not reasons:
            reasons.append("默认推荐")

        return "; ".join(reasons)

    def record_tool_execution(
        self,
        tool_name: str,
        success: bool,
        execution_time: float,
    ) -> None:
        """记录工具执行结果"""
        if tool_name not in self.metrics:
            self.metrics[tool_name] = ToolPerformanceMetrics(tool_name=tool_name)

        metrics = self.metrics[tool_name]
        metrics.total_calls += 1
        metrics.total_execution_time += execution_time
        metrics.last_used = datetime.now().isoformat()

        if success:
            metrics.successful_calls += 1
        else:
            metrics.failed_calls += 1

        # 更新统计指标
        metrics.average_execution_time = (
            metrics.total_execution_time / metrics.total_calls
        )
        metrics.success_rate = metrics.successful_calls / metrics.total_calls

        self.logger.info(
            f"记录工具执行: {tool_name}, 成功: {success}, 耗时: {execution_time:.2f}秒"
        )

        self._save_metrics()

    def get_usage_stats(self) -> List[ToolUsageStats]:
        """获取工具使用统计"""
        stats = []

        for tool_name, metrics in self.metrics.items():
            stats.append(
                ToolUsageStats(
                    tool_name=tool_name,
                    usage_count=metrics.total_calls,
                    success_rate=metrics.success_rate,
                    avg_execution_time=metrics.average_execution_time,
                    last_used=metrics.last_used,
                )
            )

        return stats

    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []

        for tool_name, metrics in self.metrics.items():
            # 成功率低的工具
            if metrics.total_calls >= 5 and metrics.success_rate < 0.5:
                suggestions.append(
                    f"工具 '{tool_name}' 成功率较低 ({metrics.success_rate:.1%})，"
                    f"建议检查配置或考虑替换"
                )

            # 执行时间长的工具
            if metrics.total_calls >= 5 and metrics.average_execution_time > 10.0:
                suggestions.append(
                    f"工具 '{tool_name}' 执行时间较长 "
                    f"({metrics.average_execution_time:.2f}秒)，"
                    f"建议优化或考虑超时设置"
                )

        if not suggestions:
            suggestions.append("所有工具运行良好，暂无优化建议")

        return suggestions

    def reset_metrics(self, tool_name: Optional[str] = None) -> None:
        """重置工具性能指标"""
        if tool_name:
            if tool_name in self.metrics:
                del self.metrics[tool_name]
                self.logger.info(f"已重置工具 '{tool_name}' 的性能指标")
        else:
            self.metrics.clear()
            self.logger.info("已重置所有工具的性能指标")

        self._save_metrics()

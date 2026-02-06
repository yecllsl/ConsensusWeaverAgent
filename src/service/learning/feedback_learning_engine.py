import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class UserFeedback:
    """用户反馈"""

    session_id: int
    question: str
    selected_tools: List[str]
    preferred_tool: str
    rating: float
    comments: Optional[str] = None


@dataclass
class UserPreference:
    """用户偏好"""

    question_type: str
    preferred_tools: List[str]
    tool_weights: Dict[str, float]
    last_updated: datetime


class FeedbackLearningEngine:
    """反馈学习引擎"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.preferences_file = os.path.join(data_dir, "user_preferences.json")
        self.feedback_file = os.path.join(data_dir, "user_feedback.json")
        self.preferences: Dict[str, UserPreference] = {}
        self._ensure_data_dir()
        self._load_preferences()

    def _ensure_data_dir(self) -> None:
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def collect_feedback(self, feedback: UserFeedback) -> None:
        """收集用户反馈"""
        self._save_feedback_to_file(feedback)
        self._update_preferences(feedback)

    def _save_feedback_to_file(self, feedback: UserFeedback) -> None:
        """保存反馈到文件"""
        feedbacks = []
        if os.path.exists(self.feedback_file):
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)

        feedback_dict = {
            "session_id": feedback.session_id,
            "question": feedback.question,
            "selected_tools": feedback.selected_tools,
            "preferred_tool": feedback.preferred_tool,
            "rating": feedback.rating,
            "comments": feedback.comments,
        }

        feedbacks.append(feedback_dict)

        with open(self.feedback_file, "w", encoding="utf-8") as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=2)

    def _update_preferences(self, feedback: UserFeedback) -> None:
        """更新用户偏好"""
        question_type = self._classify_question(feedback.question)

        if question_type not in self.preferences:
            self.preferences[question_type] = UserPreference(
                question_type=question_type,
                preferred_tools=[],
                tool_weights={},
                last_updated=datetime.now(),
            )

        preference = self.preferences[question_type]

        if feedback.preferred_tool not in preference.tool_weights:
            preference.tool_weights[feedback.preferred_tool] = 0.0

        preference.tool_weights[feedback.preferred_tool] += feedback.rating

        total_weight = sum(preference.tool_weights.values())
        for tool in preference.tool_weights:
            preference.tool_weights[tool] /= total_weight

        preference.last_updated = datetime.now()

        self._save_preferences()

    def get_recommended_tools(self, question: str, max_tools: int = 3) -> List[str]:
        """获取推荐的工具"""
        question_type = self._classify_question(question)

        if question_type not in self.preferences:
            return []

        preference = self.preferences[question_type]

        sorted_tools = sorted(
            preference.tool_weights.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [tool for tool, _ in sorted_tools[:max_tools]]

    def _classify_question(self, question: str) -> str:
        """分类问题"""
        if any(keyword in question.lower() for keyword in ["代码", "编程", "code"]):
            return "code"
        elif any(
            keyword in question.lower()
            for keyword in ["分析", "比较", "analyze", "compare"]
        ):
            return "analysis"
        else:
            return "general"

    def _load_preferences(self) -> None:
        """加载用户偏好"""
        if not os.path.exists(self.preferences_file):
            return

        with open(self.preferences_file, "r", encoding="utf-8") as f:
            preferences_dict = json.load(f)

        for key, value in preferences_dict.items():
            self.preferences[key] = UserPreference(
                question_type=value["question_type"],
                preferred_tools=value["preferred_tools"],
                tool_weights=value["tool_weights"],
                last_updated=datetime.fromisoformat(value["last_updated"]),
            )

    def _save_preferences(self) -> None:
        """保存用户偏好"""
        preferences_dict = {}
        for key, value in self.preferences.items():
            preferences_dict[key] = {
                "question_type": value.question_type,
                "preferred_tools": value.preferred_tools,
                "tool_weights": value.tool_weights,
                "last_updated": value.last_updated.isoformat(),
            }

        with open(self.preferences_file, "w", encoding="utf-8") as f:
            json.dump(preferences_dict, f, ensure_ascii=False, indent=2)

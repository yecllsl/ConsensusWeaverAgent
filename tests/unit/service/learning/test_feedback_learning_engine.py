import json
import os
from datetime import datetime

import pytest

from src.service.learning.feedback_learning_engine import (
    FeedbackLearningEngine,
    UserFeedback,
    UserPreference,
)


@pytest.fixture
def temp_data_dir(tmp_path):
    """临时数据目录"""
    return str(tmp_path)


class TestUserFeedback:
    """测试UserFeedback数据类"""

    def test_user_feedback_creation(self) -> None:
        """测试创建用户反馈"""
        feedback = UserFeedback(
            session_id=1,
            question="如何编写Python代码？",
            selected_tools=["iflow", "codebuddy"],
            preferred_tool="codebuddy",
            rating=5.0,
            comments="回答很好",
        )

        assert feedback.session_id == 1
        assert feedback.question == "如何编写Python代码？"
        assert feedback.selected_tools == ["iflow", "codebuddy"]
        assert feedback.preferred_tool == "codebuddy"
        assert feedback.rating == 5.0
        assert feedback.comments == "回答很好"

    def test_user_feedback_without_comments(self) -> None:
        """测试创建不带评论的用户反馈"""
        feedback = UserFeedback(
            session_id=1,
            question="测试问题",
            selected_tools=["iflow"],
            preferred_tool="iflow",
            rating=4.0,
        )

        assert feedback.comments is None


class TestUserPreference:
    """测试UserPreference数据类"""

    def test_user_preference_creation(self) -> None:
        """测试创建用户偏好"""
        preference = UserPreference(
            question_type="code",
            preferred_tools=["codebuddy"],
            tool_weights={"codebuddy": 0.8, "iflow": 0.2},
            last_updated=datetime.now(),
        )

        assert preference.question_type == "code"
        assert preference.preferred_tools == ["codebuddy"]
        assert preference.tool_weights == {"codebuddy": 0.8, "iflow": 0.2}


class TestFeedbackLearningEngine:
    """测试反馈学习引擎"""

    def test_init(self, temp_data_dir) -> None:
        """测试初始化"""
        engine = FeedbackLearningEngine(temp_data_dir)
        assert engine.preferences == {}
        assert os.path.exists(temp_data_dir)

    def test_collect_feedback(self, temp_data_dir) -> None:
        """测试收集用户反馈"""
        engine = FeedbackLearningEngine(temp_data_dir)

        feedback = UserFeedback(
            session_id=1,
            question="如何编写Python代码？",
            selected_tools=["iflow", "codebuddy"],
            preferred_tool="codebuddy",
            rating=5.0,
        )

        engine.collect_feedback(feedback)

        assert "code" in engine.preferences
        assert "codebuddy" in engine.preferences["code"].tool_weights

    def test_update_preferences(self, temp_data_dir) -> None:
        """测试更新用户偏好"""
        engine = FeedbackLearningEngine(temp_data_dir)

        feedback1 = UserFeedback(
            session_id=1,
            question="如何编写Python代码？",
            selected_tools=["codebuddy"],
            preferred_tool="codebuddy",
            rating=5.0,
        )

        feedback2 = UserFeedback(
            session_id=2,
            question="如何编写Java代码？",
            selected_tools=["codebuddy"],
            preferred_tool="codebuddy",
            rating=4.0,
        )

        engine.collect_feedback(feedback1)
        engine.collect_feedback(feedback2)

        preference = engine.preferences["code"]
        assert "codebuddy" in preference.tool_weights
        assert preference.tool_weights["codebuddy"] == 1.0

    def test_get_recommended_tools(self, temp_data_dir) -> None:
        """测试获取推荐工具"""
        engine = FeedbackLearningEngine(temp_data_dir)

        feedback = UserFeedback(
            session_id=1,
            question="如何编写Python代码？",
            selected_tools=["codebuddy"],
            preferred_tool="codebuddy",
            rating=5.0,
        )

        engine.collect_feedback(feedback)

        recommended = engine.get_recommended_tools("如何编写C++代码？")
        assert "codebuddy" in recommended

    def test_get_recommended_tools_no_preference(self, temp_data_dir) -> None:
        """测试获取推荐工具（无偏好）"""
        engine = FeedbackLearningEngine(temp_data_dir)

        recommended = engine.get_recommended_tools("测试问题")
        assert recommended == []

    def test_classify_question_code(self, temp_data_dir) -> None:
        """测试分类问题（代码）"""
        engine = FeedbackLearningEngine(temp_data_dir)

        question_type = engine._classify_question("如何编写Python代码？")
        assert question_type == "code"

    def test_classify_question_analysis(self, temp_data_dir) -> None:
        """测试分类问题（分析）"""
        engine = FeedbackLearningEngine(temp_data_dir)

        question_type = engine._classify_question("请分析这两个方案的优劣")
        assert question_type == "analysis"

    def test_classify_question_general(self, temp_data_dir) -> None:
        """测试分类问题（通用）"""
        engine = FeedbackLearningEngine(temp_data_dir)

        question_type = engine._classify_question("今天天气怎么样？")
        assert question_type == "general"

    def test_save_and_load_preferences(self, temp_data_dir) -> None:
        """测试保存和加载用户偏好"""
        engine1 = FeedbackLearningEngine(temp_data_dir)

        feedback = UserFeedback(
            session_id=1,
            question="如何编写Python代码？",
            selected_tools=["codebuddy"],
            preferred_tool="codebuddy",
            rating=5.0,
        )

        engine1.collect_feedback(feedback)

        engine2 = FeedbackLearningEngine(temp_data_dir)
        assert "code" in engine2.preferences
        assert "codebuddy" in engine2.preferences["code"].tool_weights

    def test_multiple_feedbacks_same_type(self, temp_data_dir) -> None:
        """测试多个相同类型的反馈"""
        engine = FeedbackLearningEngine(temp_data_dir)

        feedbacks = [
            UserFeedback(
                session_id=i,
                question=f"如何编写Python代码{i}？",
                selected_tools=["codebuddy"],
                preferred_tool="codebuddy",
                rating=5.0,
            )
            for i in range(3)
        ]

        for feedback in feedbacks:
            engine.collect_feedback(feedback)

        preference = engine.preferences["code"]
        assert "codebuddy" in preference.tool_weights
        assert preference.tool_weights["codebuddy"] == 1.0

    def test_feedback_file_creation(self, temp_data_dir) -> None:
        """测试反馈文件创建"""
        engine = FeedbackLearningEngine(temp_data_dir)

        feedback = UserFeedback(
            session_id=1,
            question="测试问题",
            selected_tools=["iflow"],
            preferred_tool="iflow",
            rating=4.0,
        )

        engine.collect_feedback(feedback)

        feedback_file = os.path.join(temp_data_dir, "user_feedback.json")
        assert os.path.exists(feedback_file)

        with open(feedback_file, "r", encoding="utf-8") as f:
            feedbacks = json.load(f)

        assert len(feedbacks) == 1
        assert feedbacks[0]["session_id"] == 1

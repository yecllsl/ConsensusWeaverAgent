#!/usr/bin/env python3
"""
测试分歧点识别功能
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# 将项目根目录添加到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from src.core.analyzer.consensus_analyzer import ConsensusAnalyzer


def test_difference_identification():
    """测试分歧点识别功能"""
    # 创建模拟配置管理器
    mock_config_manager = MagicMock()
    mock_config = MagicMock()
    mock_config_manager.get_config.return_value = mock_config

    # 创建模拟LLM服务
    mock_llm_service = MagicMock()

    # 模拟LLM返回带有代码块标记的响应
    mock_response = """```json
[
  {
    "content": "The first answer lists six collaboration modes, including centralized, "
                "distributed, hierarchical, alliance, competitive and mixed.",
    "sources": ["iflow", "codebuddy", "qwen"]
  },
  {
    "content": "The second answer also mentions six collaboration modes: hierarchical, "
                "equal, pipeline, competition, consensus and mixed.",
    "sources": ["iflow", "codebuddy"]
  }
]
```"""

    mock_llm_service.generate_response.return_value = mock_response

    # 创建模拟数据管理器
    mock_data_manager = MagicMock()

    # 创建ConsensusAnalyzer实例
    analyzer = ConsensusAnalyzer(mock_llm_service, mock_data_manager)

    # 模拟工具结果
    tool_results = [
        {
            "tool_name": "iflow",
            "answer": "This is a test answer from iflow.",
            "success": True,
        },
        {
            "tool_name": "codebuddy",
            "answer": "This is a test answer from codebuddy.",
            "success": True,
        },
        {
            "tool_name": "qwen",
            "answer": "This is a test answer from qwen.",
            "success": True,
        },
    ]

    try:
        # 调用分歧点识别方法
        differences = analyzer._identify_differences(tool_results)
        print("测试成功！")
        print(f"解析后的分歧点: {json.dumps(differences, indent=2)}")
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_difference_identification()

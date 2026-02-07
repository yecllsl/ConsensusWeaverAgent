"""领域模型层 - 定义业务实体

本模块定义了ConsensusWeaverAgent的核心业务实体：
- Session: 会话实体
- ToolResult: 工具结果实体
- AnalysisResult: 分析结果实体
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Session:
    """会话实体

    表示一个完整的问答会话，包含原始问题、优化后问题、
    时间戳和完成状态等信息。
    """

    id: Optional[int] = None
    original_question: str = ""
    refined_question: Optional[str] = None
    timestamp: Optional[datetime] = None
    completed: bool = False

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ToolResult:
    """工具结果实体

    表示单个工具执行的结果，包含工具名称、执行状态、
    答案、错误信息和执行时间等信息。
    """

    id: Optional[int] = None
    session_id: int = 0
    tool_name: str = ""
    success: bool = False
    answer: str = ""
    error_message: str = ""
    execution_time: float = 0.0
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class AnalysisResult:
    """分析结果实体

    表示共识分析的结果，包含相似度矩阵、共识分数、
    关键点、分歧点、综合总结和最终结论等信息。
    """

    id: Optional[int] = None
    session_id: int = 0
    similarity_matrix: List[List[float]] = field(default_factory=list)
    consensus_scores: Dict[str, float] = field(default_factory=dict)
    key_points: List[Dict[str, Any]] = field(default_factory=list)
    differences: List[Dict[str, Any]] = field(default_factory=list)
    comprehensive_summary: str = ""
    final_conclusion: str = ""
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

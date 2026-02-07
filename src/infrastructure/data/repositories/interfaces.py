"""仓库接口层 - 定义数据访问抽象接口

本模块定义了所有数据仓库的抽象接口，遵循依赖倒置原则（DIP），
确保高层模块不依赖低层模块，而是依赖抽象。
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from src.models.entities import AnalysisResult, Session, ToolResult

T = TypeVar("T")


class IRepository(Generic[T], ABC):
    """通用仓库接口

    定义了所有仓库必须实现的基本CRUD操作。
    """

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        """根据ID获取实体"""
        pass

    @abstractmethod
    async def get_all(self) -> List[T]:
        """获取所有实体"""
        pass

    @abstractmethod
    async def add(self, entity: T) -> int:
        """添加实体，返回ID"""
        pass

    @abstractmethod
    async def add_batch(self, entities: List[T]) -> List[int]:
        """批量添加实体，返回ID列表"""
        pass

    @abstractmethod
    async def update(self, entity: T) -> None:
        """更新实体"""
        pass

    @abstractmethod
    async def delete(self, id: int) -> None:
        """删除实体"""
        pass


class ISessionRepository(IRepository[Session]):
    """会话仓库接口

    定义会话数据访问的特定操作。
    """

    @abstractmethod
    async def get_recent(self, limit: int = 10) -> List[Session]:
        """获取最近的会话"""
        pass

    @abstractmethod
    async def get_by_question(self, question: str) -> Optional[Session]:
        """根据问题获取会话"""
        pass


class IToolResultRepository(IRepository[ToolResult]):
    """工具结果仓库接口

    定义工具结果数据访问的特定操作。
    """

    @abstractmethod
    async def get_by_session_id(self, session_id: int) -> List[ToolResult]:
        """根据会话ID获取工具结果"""
        pass

    @abstractmethod
    async def save_batch_for_session(
        self, session_id: int, results: List[ToolResult]
    ) -> List[int]:
        """批量保存会话的工具结果"""
        pass


class IAnalysisResultRepository(IRepository[AnalysisResult]):
    """分析结果仓库接口

    定义分析结果数据访问的特定操作。
    """

    @abstractmethod
    async def get_by_session_id(self, session_id: int) -> Optional[AnalysisResult]:
        """根据会话ID获取分析结果"""
        pass


class IUnitOfWork(ABC):
    """工作单元接口（事务管理）

    定义事务管理的基本操作，确保多个操作在一个事务中执行，
    要么全部成功，要么全部回滚。
    """

    @abstractmethod
    async def __aenter__(self) -> "IUnitOfWork":
        """进入事务上下文"""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """退出事务上下文"""
        pass

    @abstractmethod
    async def commit(self) -> None:
        """提交事务"""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """回滚事务"""
        pass

    @property
    @abstractmethod
    def sessions(self) -> ISessionRepository:
        """会话仓库"""
        pass

    @property
    @abstractmethod
    def tool_results(self) -> IToolResultRepository:
        """工具结果仓库"""
        pass

    @property
    @abstractmethod
    def analysis_results(self) -> IAnalysisResultRepository:
        """分析结果仓库"""
        pass

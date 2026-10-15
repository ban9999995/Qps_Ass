"""FastAPI 依赖注入。"""

from functools import lru_cache

from app.repository.memory import InMemoryRepository
from app.service.services import OperationsService


@lru_cache
def get_repository() -> InMemoryRepository:
    """返回进程级演示仓储；生产环境替换为 MySQL 实现。"""
    return InMemoryRepository()


def get_service() -> OperationsService:
    """构造业务服务并注入仓储。"""
    return OperationsService(get_repository())

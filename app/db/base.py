"""SQLAlchemy 异步数据库基类和会话工厂。"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.shared.config import get_settings


class Base(DeclarativeBase):
    """所有 ORM 实体的声明式基类。"""


engine = create_async_engine(get_settings().database_url, echo=False, pool_pre_ping=True)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """按请求创建并关闭异步数据库会话。"""
    async with SessionFactory() as session:
        yield session

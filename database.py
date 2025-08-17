from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# SQLite异步数据库URL
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./chat_config.db"

# 创建异步数据库引擎
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,  # 设置为True可以看到SQL语句
    future=True
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 创建基础模型类
Base = declarative_base()

# 异步获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# 异步创建数据库表
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 异步删除所有表（用于测试）
async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

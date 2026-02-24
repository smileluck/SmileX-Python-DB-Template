"""
异步数据库连接管理器
提供SQLAlchemy异步数据库连接池和会话管理
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Any
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import SessionTransactionOrigin
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from sqlalchemy import create_engine, text

from sqlalchemy.exc import SQLAlchemyError
import asyncio
import logging

from ..config import DatabaseModel

logger = logging.getLogger(__name__)


async def check_db_connection(engine: AsyncEngine) -> bool:
    """
    验证异步数据库引擎的连接是否成功

    Args:
        engine: 创建好的异步引擎对象

    Returns:
        bool: 连接成功返回 True，失败返回 False
    """
    try:
        # 获取异步连接（核心步骤：真正建立数据库连接）
        async with engine.connect() as conn:
            # 执行轻量级查询（不同数据库通用的测试语句）
            # SELECT 1 是大多数数据库都支持的空查询，无副作用
            result = await conn.execute(text("SELECT 1"))
            # 获取查询结果，验证执行成功
            row = result.scalar()
            if row == 1:
                print("✅ 数据库连接成功！")
                return True
    except SQLAlchemyError as e:
        # 捕获所有 SQLAlchemy 相关异常（认证失败、连接超时、数据库不存在等）
        print(f"❌ 数据库连接失败：{str(e)}")
        return False
    except Exception as e:
        # 捕获其他未知异常
        print(f"❌ 连接过程中发生未知错误：{str(e)}")
        return False
    finally:
        # 关闭引擎（可选，根据实际场景决定是否关闭）
        await engine.dispose()


class AsyncDatabaseManager:
    """
    异步数据库连接管理器

    特性:
    - 支持MySQL和PostgreSQL异步连接
    - 完整的连接池配置
    - 支持事务和自动提交
    - 完善的异常处理和日志记录
    - 兼容FastAPI的依赖注入

    使用示例:
    ```python
    # 初始化
    manager = AsyncDatabaseManager()
    await manager.init_pool(settings)

    # 获取会话
    async with manager.get_session() as session:
        result = await session.execute(select(User))

    # FastAPI依赖注入
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with manager.get_session() as session:
            yield session
    ```
    """

    def __init__(self, settings: Optional[DatabaseModel] = None):
        """
        初始化异步数据库管理器

        Args:
            settings: 数据库配置实例，若为None则使用默认配置
        """
        self._settings = settings
        self._engine: Optional[AsyncEngine] = None
        self._session_maker: Optional[async_sessionmaker[AsyncSession]] = None
        self._is_async = True

    async def init_pool(self, settings: Optional[DatabaseModel] = None) -> None:
        """
        初始化异步数据库连接池

        Args:
            settings: 数据库配置实例，若为None则使用默认配置或已设置配置

        Raises:
            ValueError: 未提供配置且未初始化配置
            RuntimeError: 连接池已初始化
        """
        if self._engine is not None:
            logger.warning("异步数据库连接池已初始化，跳过重复初始化")
            return

        if settings is not None:
            self._settings = settings
        elif self._settings is None:
            self._settings = DatabaseModel()

        if self._settings.is_sync:
            logger.warning("当前配置为同步模式，将使用异步驱动创建连接池")

        url = self._settings.build_url(async_mode=True)
        connect_args = self._build_connect_args()

        logger.info(
            f"初始化异步数据库连接池: {self._settings.type.value}+"
            f"{self._settings.async_driver}://"
            f"{self._settings.host}:{self._settings.port}/{self._settings.database}"
        )

        self._engine = create_async_engine(
            url,
            poolclass=(
                AsyncAdaptedQueuePool if self._settings.pool_size > 0 else NullPool
            ),
            pool_size=self._settings.pool_size,
            max_overflow=self._settings.max_overflow,
            pool_recycle=self._settings.pool_recycle,
            pool_timeout=self._settings.pool_timeout,
            pool_pre_ping=self._settings.pool_pre_ping,
            pool_use_lifo=self._settings.pool_use_lifo,
            pool_reset_on_return=self._settings.pool_reset_on_return,
            echo=self._settings.echo,
            echo_pool=self._settings.echo_pool,
            connect_args=connect_args,
            isolation_level=self._settings.isolation_level,
        )

        # 验证数据库连接
        if not await check_db_connection(self._engine):
            raise RuntimeError("数据库连接验证失败，无法初始化连接池")

        self._session_maker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

        logger.info(
            f"异步数据库连接池初始化成功: pool_size={self._settings.pool_size}, "
            f"max_overflow={self._settings.max_overflow}"
        )

    def _build_connect_args(self) -> dict[str, Any]:
        """构建连接参数"""
        connect_args: dict[str, Any] = {}

        if self._settings.type.value == "mysql":
            connect_args["init_command"] = (
                f"SET sql_mode='{self._settings.mysql_sql_mode}'"
            )

        return connect_args

    async def close_pool(self) -> None:
        """
        关闭异步数据库连接池

        释放所有连接并清理资源
        """
        if self._engine is None:
            logger.warning("异步数据库连接池未初始化，无需关闭")
            return

        logger.info("正在关闭异步数据库连接池...")

        await self._engine.dispose()
        self._engine = None
        self._session_maker = None

        logger.info("异步数据库连接池已关闭")

    @asynccontextmanager
    async def get_session_cr(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取异步数据库会话的上下文管理器

        Yields:
            SQLAlchemy AsyncSession实例

        Raises:
            RuntimeError: 连接池未初始化

        Example:
            ```python
            async with manager.get_session() as session:
                result = await session.execute(select(User).where(User.id == 1))
                user = result.scalar_one()
            ```
        """
        if self._session_maker is None:
            raise RuntimeError("异步数据库连接池未初始化，请先调用init_pool()方法")

        async with self._session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"异步数据库会话错误: {e}", exc_info=True)
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取异步数据库会话的上下文管理器

        Yields:
            SQLAlchemy AsyncSession实例

        Raises:
            RuntimeError: 连接池未初始化

        Example:
            ```python
            async with manager.get_session() as session:
                result = await session.execute(select(User).where(User.id == 1))
                user = result.scalar_one()
            ```
        """
        if self._session_maker is None:
            raise RuntimeError("异步数据库连接池未初始化，请先调用init_pool()方法")

        async with self._session_maker() as session:
            yield session

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库原始连接的上下文管理器

        Yields:
            异步DBAPI连接实例

        Raises:
            RuntimeError: 连接池未初始化
        """
        if self._engine is None:
            raise RuntimeError("异步数据库连接池未初始化，请先调用init_pool()方法")

        async with self._engine.connect() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        异步事务上下文管理器

        提供显式事务控制，支持嵌套事务

        Yields:
            SQLAlchemy AsyncSession实例

        Example:
            ```python
            async with manager.transaction() as session:
                user.name = "新名称"
                # 自动提交
            ```
        """
        if self._session_maker is None:
            raise RuntimeError("异步数据库连接池未初始化，请先调用init_pool()方法")

        async with self._session_maker() as session:
            try:
                async with session.begin():
                    yield session
            except Exception as e:
                logger.error(f"异步事务执行错误: {e}", exc_info=True)
                raise

    async def execute_raw_sql(self, sql: str, params: Optional[dict] = None) -> Any:
        """
        执行原始SQL语句

        Args:
            sql: SQL语句
            params: 参数字典

        Returns:
            执行结果

        Raises:
            RuntimeError: 连接池未初始化
        """
        from sqlalchemy import text

        async with self.get_session() as session:
            result = await session.execute(text(sql), params or {})
            await session.commit()
            return result

    async def health_check(self) -> bool:
        """
        执行数据库健康检查

        Returns:
            连接是否健康
        """
        try:
            async with self.get_connection() as conn:
                from sqlalchemy import text

                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False

    @property
    def engine(self) -> Optional[AsyncEngine]:
        """获取SQLAlchemy异步引擎实例"""
        return self._engine

    @property
    def session_maker(self) -> Optional[async_sessionmaker[AsyncSession]]:
        """获取会话工厂"""
        return self._session_maker

    @property
    def settings(self) -> DatabaseModel:
        """获取数据库配置"""
        return self._settings

    @property
    def is_initialized(self) -> bool:
        """检查连接池是否已初始化"""
        return self._engine is not None

    async def __aenter__(self) -> "AsyncDatabaseManager":
        """异步上下文管理器入口"""
        await self.init_pool()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器退出"""
        await self.close_pool()

    def __del__(self):
        """析构函数，确保资源释放"""
        try:
            if self._engine is not None:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._engine.dispose())
                else:
                    loop.run_until_complete(self._engine.dispose())
        except Exception:
            pass


# 全局异步数据库管理器实例
async_db_manager = AsyncDatabaseManager()


async def init_pool(settings: Optional[DatabaseModel] = None) -> None:
    """
    初始化异步数据库连接池

    兼容旧接口

    Args:
        settings: 数据库配置实例
    """
    await async_db_manager.init_pool(settings)


async def close_pool() -> None:
    """关闭异步数据库连接池"""
    await async_db_manager.close_pool()


async def get_session_cr() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话的生成器函数

    兼容旧接口

    Yields:
        SQLAlchemy AsyncSession实例
    """
    async with async_db_manager.get_session_cr() as session:
        yield session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话的生成器函数

    兼容旧接口

    Yields:
        SQLAlchemy AsyncSession实例
    """
    async with async_db_manager.get_session() as session:
        yield session

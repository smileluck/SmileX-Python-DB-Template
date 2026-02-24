"""
同步数据库连接管理器
提供SQLAlchemy同步数据库连接池和会话管理
"""

from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event, Result
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool, NullPool
import logging

from ..config import DatabaseModel

logger = logging.getLogger(__name__)


class SyncDatabaseManager:
    """
    同步数据库连接管理器

    特性:
    - 支持MySQL和PostgreSQL同步连接
    - 完整的连接池配置
    - 线程安全的会话管理
    - 支持事务和自动提交
    - 完善的异常处理

    使用示例:
    ```python
    # 初始化
    manager = SyncDatabaseManager()
    manager.init_pool(settings)

    # 获取会话
    with manager.get_session() as session:
        users = session.query(User).all()

    # 原始连接
    with manager.get_connection() as conn:
        conn.execute(text("SELECT 1"))
    ```
    """

    def __init__(self, settings: Optional[DatabaseModel] = None):
        """
        初始化同步数据库管理器

        Args:
            settings: 数据库配置实例，若为None则使用默认配置
        """
        self._settings = settings
        self._engine = None
        self._session_factory = None
        self._scoped_session = None

    def init_pool(self, settings: Optional[DatabaseModel] = None) -> None:
        """
        初始化数据库连接池

        Args:
            settings: 数据库配置实例，若为None则使用默认配置或已设置配置

        Raises:
            ValueError: 未提供配置且未初始化配置
            RuntimeError: 连接池已初始化
        """
        if self._engine is not None:
            logger.warning("数据库连接池已初始化，跳过重复初始化")
            return

        if settings is not None:
            self._settings = settings
        elif self._settings is None:
            self._settings = DatabaseModel()

        if self._settings.is_async:
            logger.warning("当前配置为异步模式，将使用同步驱动创建连接池")

        url = self._settings.build_url(async_mode=False)
        connect_args = self._build_connect_args()

        logger.info(
            f"初始化同步数据库连接池: {self._settings.type.value}://"
            f"{self._settings.host}:{self._settings.port}/{self._settings.database}"
        )

        self._engine = create_engine(
            url,
            poolclass=QueuePool,
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

        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

        self._scoped_session = scoped_session(self._session_factory)

        self._setup_pool_listeners()

        logger.info(
            f"同步数据库连接池初始化成功: pool_size={self._settings.pool_size}, "
            f"max_overflow={self._settings.max_overflow}"
        )

    def _build_connect_args(self) -> dict:
        """构建连接参数"""
        connect_args = {}

        if self._settings.type.value == "mysql":
            connect_args["init_command"] = (
                f"SET sql_mode='{self._settings.mysql_sql_mode}'"
            )

        return connect_args

    def _setup_pool_listeners(self) -> None:
        """设置连接池事件监听器"""
        if not self._engine:
            return

        @event.listens_for(self._engine.pool, "connect")
        def on_connect(dbapi_connection, connection_record):
            """连接建立时的处理"""
            connection_record.info["connected_at"] = __import__("time").time()
            logger.debug(f"数据库连接建立: {connection_record.connection_info}")

        @event.listens_for(self._engine.pool, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """连接检出时的处理"""
            connection_record.info["checked_out_at"] = __import__("time").time()
            logger.debug(f"数据库连接检出: {connection_record.connection_info}")

        @event.listens_for(self._engine.pool, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """连接归还时的处理"""
            if "checked_out_at" in connection_record.info:
                duration = (
                    __import__("time").time() - connection_record.info["checked_out_at"]
                )
                logger.debug(f"数据库连接归还: 使用时长={duration:.2f}秒")

        @event.listens_for(self._engine.pool, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            """连接失效时的处理"""
            logger.warning(f"数据库连接失效: {exception}", exc_info=exception)

    def close_pool(self) -> None:
        """
        关闭数据库连接池

        释放所有连接并清理资源
        """
        if self._engine is None:
            logger.warning("数据库连接池未初始化，无需关闭")
            return

        logger.info("正在关闭同步数据库连接池...")

        if self._scoped_session:
            self._scoped_session.remove()
            self._scoped_session.close()

        self._engine.dispose()
        self._engine = None
        self._session_factory = None
        self._scoped_session = None

        logger.info("同步数据库连接池已关闭")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话的上下文管理器

        Yields:
            SQLAlchemy Session实例

        Raises:
            RuntimeError: 连接池未初始化

        Example:
            ```python
            with manager.get_session() as session:
                user = session.get(User, 1)
                session.commit()
            ```
        """
        if self._session_factory is None:
            raise RuntimeError("数据库连接池未初始化，请先调用init_pool()方法")

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话错误: {e}", exc_info=True)
            raise
        finally:
            session.close()

    @contextmanager
    def get_connection(self) -> Generator:
        """
        获取数据库原始连接的上下文管理器

        Yields:
            DBAPI连接实例

        Raises:
            RuntimeError: 连接池未初始化
        """
        if self._engine is None:
            raise RuntimeError("数据库连接池未初始化，请先调用init_pool()方法")

        with self._engine.connect() as conn:
            yield conn

    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """
        事务上下文管理器

        提供显式事务控制，支持嵌套事务

        Yields:
            SQLAlchemy Session实例

        Example:
            ```python
            with manager.transaction() as session:
                user.name = "新名称"
                # 自动提交
            ```
        """
        if self._session_factory is None:
            raise RuntimeError("数据库连接池未初始化，请先调用init_pool()方法")

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"事务执行错误: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def get_scoped_session(self) -> scoped_session:
        """
        获取作用域会话工厂

        Returns:
            SQLAlchemy scoped_session实例

        Raises:
            RuntimeError: 连接池未初始化
        """
        if self._scoped_session is None:
            raise RuntimeError("数据库连接池未初始化，请先调用init_pool()方法")
        return self._scoped_session

    def execute_raw_sql(self, sql: str, params: Optional[dict] = None) -> Result:
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
        with self.get_session() as session:
            from sqlalchemy import text

            result = session.execute(text(sql), params or {})
            session.commit()
            return result

    @property
    def engine(self):
        """获取SQLAlchemy引擎实例"""
        return self._engine

    @property
    def settings(self) -> DatabaseModel:
        """获取数据库配置"""
        return self._settings

    @property
    def is_initialized(self) -> bool:
        """检查连接池是否已初始化"""
        return self._engine is not None

    def __enter__(self) -> "SyncDatabaseManager":
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器退出"""
        self.close_pool()

    def __del__(self):
        """析构函数，确保资源释放"""
        try:
            if self._engine is not None:
                self.close_pool()
        except Exception:
            pass


# 全局同步数据库管理器实例
sync_db_manager = SyncDatabaseManager()


def get_sync_session() -> Generator[Session, None, None]:
    """
    获取同步数据库会话的生成器函数

    兼容旧接口

    Yields:
        SQLAlchemy Session实例
    """
    if not sync_db_manager.is_initialized:
        sync_db_manager.init_pool()

    with sync_db_manager.get_session() as session:
        yield session

"""
通用数据库接口模块
支持SQLAlchemy2.0,同步/异步连接,连接池,Alembic迁移

特性:
- SQLAlchemy 2.0 完整支持
- 同步和异步数据库连接
- 连接池管理
- MySQL和PostgreSQL双数据库支持
- Alemic迁移支持
- Pydantic配置管理

快速开始:
```python
from database import (
    AsyncDatabaseManager,
    SyncDatabaseManager,
    DatabaseModel,
    Base,
)

# 异步模式
async_manager = AsyncDatabaseManager()
await async_manager.init_pool(db_settings.database)

async with async_manager.get_session() as session:
    # 执行数据库操作
    pass

# 同步模式
sync_manager = SyncDatabaseManager()
sync_manager.init_pool(db_settings.database)

with sync_manager.get_session() as session:
    # 执行数据库操作
    pass
```
"""

from .config import (
    DatabaseModel,
    DatabaseType,
    DatabaseDriver,
    ConnectionMode,
    settings as db_settings,
)

from .manager.async_manager import (
    AsyncDatabaseManager,
    async_db_manager,
    init_pool as init_async_pool,
    close_pool as close_async_pool,
    get_session,
    get_session_cr,
)

from .manager.sync_manager import (
    SyncDatabaseManager,
    sync_db_manager,
    get_sync_session,
)

from .utils.url_builder import (
    DatabaseURLBuilder,
    DatabaseCredentials,
    DriverType,
    build_database_url,
)

from .models.base import (
    Base,
    DataClassBase,
    MappedBase,
    snowflake_id_key,
    UserMixin,
    DateTimeMixin,
    LogicMixin,
)

from .models.dataclasses import (
    IpInfo,
    UserAgentInfo,
    AccessToken,
    RefreshToken,
    SnowflakeInfo,
)

__all__ = [
    # 配置相关
    "DatabaseModel",
    "DatabaseType",
    "DatabaseDriver",
    "ConnectionMode",
    "db_settings",
    # 异步管理器
    "AsyncDatabaseManager",
    "async_db_manager",
    "init_async_pool",
    "close_async_pool",
    "get_session",
    "get_session_cr",
    # 同步管理器
    "SyncDatabaseManager",
    "sync_db_manager",
    "get_sync_session",
    # URL构建器
    "DatabaseURLBuilder",
    "DatabaseCredentials",
    "DriverType",
    "build_database_url",
    # 模型基类
    "Base",
    "DataClassBase",
    "MappedBase",
    "snowflake_id_key",
    "UserMixin",
    "DateTimeMixin",
    "LogicMixin",
    # 数据类
    "IpInfo",
    "UserAgentInfo",
    "AccessToken",
    "RefreshToken",
    "SnowflakeInfo",
]

__version__ = "0.1.0"

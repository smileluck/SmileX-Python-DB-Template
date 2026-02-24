"""
数据库配置模块
提供完整的数据库配置管理，支持MySQL和PostgreSQL，同步和异步连接
"""

from typing import Any, Optional
from enum import Enum
from pydantic import Field, field_validator, BaseModel
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus


class DatabaseDriver(str, Enum):
    """数据库驱动枚举"""

    MYSQL = "mysql"
    PGSQL = "postgresql"


class DatabaseType(str, Enum):
    """数据库类型枚举"""

    MYSQL = "mysql"
    PGSQL = "postgresql"


class ConnectionMode(str, Enum):
    """连接模式枚举"""

    SYNC = "sync"
    ASYNC = "async"


class DatabaseModel(BaseModel):
    """
    数据库配置类

    支持以下特性:
    - MySQL和PostgreSQL双数据库支持
    - 同步和异步连接模式
    - 连接池配置
    - 自动URL构建
    - 完整的连接参数配置

    环境变量示例:
    DATABASE_TYPE=mysql
    DATABASE_HOST=localhost
    DATABASE_PORT=3306
    DATABASE_USER=root
    DATABASE_PASSWORD=password
    DATABASE_NAME=testdb
    DATABASE_POOL_SIZE=10
    DATABASE_MAX_OVERFLOW=20
    """

    # 数据库类型
    type: DatabaseType = DatabaseType.MYSQL

    # 连接模式
    mode: ConnectionMode = ConnectionMode.ASYNC

    # 主机配置
    host: str = Field(default="localhost", description="数据库主机地址")
    port: int = Field(default=3306, ge=1, le=65535, description="数据库端口")
    username: str = Field(default="root", description="数据库用户名")
    password: str = Field(default="", description="数据库密码")
    database: str = Field(default="testdb", description="数据库名称")

    # 连接池配置
    pool_size: int = Field(default=10, ge=1, le=100, description="连接池大小")
    max_overflow: int = Field(default=20, ge=0, le=200, description="连接池最大溢出数")
    pool_recycle: int = Field(default=3600, ge=0, description="连接回收时间(秒)")
    pool_timeout: int = Field(default=30, ge=1, description="连接超时时间(秒)")
    pool_pre_ping: bool = Field(default=True, description="连接前ping检查")
    pool_use_lifo: bool = Field(default=True, description="使用LIFO取连接策略")

    # SQLAlchemy配置
    echo: bool = Field(default=False, description="是否打印SQL语句")
    echo_pool: bool = Field(default=False, description="是否打印连接池日志")
    encoding: str = Field(default="utf8mb4", description="数据库编码")
    charset: str = Field(default="utf8mb4", description="字符集")
    collation: Optional[str] = Field(default=None, description="排序规则")
    isolation_level: Optional[str] = Field(default=None, description="事务隔离级别")
    pool_reset_on_return: str = Field(
        default="rollback", description="归还连接时的重置策略"
    )

    # MySQL特有配置
    mysql_sql_mode: str = Field(
        default="STRICT_TRANS_TABLES", description="MySQL SQL模式"
    )
    mysql_init_command: Optional[str] = Field(
        default=None, description="MySQL初始化命令"
    )

    # PostgreSQL特有配置
    # pgsql_application_name: str = Field(default="cloud-database", description="应用名称")
    pgsql_keepalives_idle: int = Field(default=0, description="Keepalive空闲时间")
    pgsql_keepalives_interval: int = Field(default=0, description="Keepalive间隔")
    pgsql_keepalives_count: int = Field(default=0, description="Keepalive重试次数")

    # 计算属性
    @property
    def driver(self) -> str:
        """获取数据库驱动类型"""
        return self.type.value

    @property
    def async_driver(self) -> str:
        """获取异步数据库驱动"""
        if self.type == DatabaseType.MYSQL:
            return "aiomysql"
        return "asyncpg"

    @property
    def sync_driver(self) -> str:
        """获取同步数据库驱动"""
        if self.type == DatabaseType.MYSQL:
            return "pymysql"
        return "psycopg2"

    @property
    def is_async(self) -> bool:
        """是否为异步模式"""
        return self.mode == ConnectionMode.ASYNC

    @property
    def is_sync(self) -> bool:
        """是否为同步模式"""
        return self.mode == ConnectionMode.SYNC

    def build_url(self, async_mode: Optional[bool] = None) -> str:
        """
        构建数据库连接URL

        Args:
            async_mode: 是否使用异步驱动，None则使用当前mode设置

        Returns:
            数据库连接URL字符串
        """
        if async_mode is None:
            async_mode = self.is_async

        driver = self.async_driver if async_mode else self.sync_driver

        # URL编码密码
        encoded_password = quote_plus(self.password)

        if self.type == DatabaseType.MYSQL:
            return (
                f"mysql+{driver}://"
                f"{self.username}:{encoded_password}@"
                f"{self.host}:{self.port}/"
                f"{self.database}"
                f"?charset={self.charset}"
            )
        else:
            # query_params = f"application_name={self.pgsql_application_name}"
            return (
                f"postgresql+{driver}://"
                f"{self.username}:{encoded_password}@"
                f"{self.host}:{self.port}/"
                f"{self.database}"
                # f"?{query_params}"
            )

    def build_connection_kwargs(self) -> dict[str, Any]:
        """
        构建数据库连接关键字参数

        Returns:
            连接参数字典
        """
        kwargs = {
            "echo": self.echo,
            "echo_pool": self.echo_pool,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_recycle": self.pool_recycle,
            "pool_timeout": self.pool_timeout,
            "pool_pre_ping": self.pool_pre_ping,
            "pool_use_lifo": self.pool_use_lifo,
            "pool_reset_on_return": self.pool_reset_on_return,
        }

        if self.type == DatabaseType.MYSQL:
            kwargs.update(
                {
                    "mysql_sql_mode": self.mysql_sql_mode,
                }
            )
            if self.mysql_init_command:
                kwargs["init_command"] = self.mysql_init_command
        else:
            # kwargs.update({
            #     "application_name": self.pgsql_application_name,
            # })
            if self.pgsql_keepalives_idle > 0:
                kwargs["keepalives_idle"] = self.pgsql_keepalives_idle
            if self.pgsql_keepalives_interval > 0:
                kwargs["keepalives_interval"] = self.pgsql_keepalives_interval
            if self.pgsql_keepalives_count > 0:
                kwargs["keepalives_count"] = self.pgsql_keepalives_count

        if self.isolation_level:
            kwargs["isolation_level"] = self.isolation_level

        return kwargs

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v: str) -> DatabaseType:
        """验证并转换数据库类型"""
        if isinstance(v, DatabaseType):
            return v
        v_lower = v.lower()
        for db_type in DatabaseType:
            if db_type.value == v_lower:
                return db_type
        raise ValueError(f"不支持的数据库类型: {v}")

    class Config:
        """Pydantic配置"""

        env_prefix = "DATABASE_"
        env_nested_delimiter = "__"
        extra = "ignore"
        case_sensitive = False


class GlobalSetting(BaseSettings):
    """全局配置类"""

    database: DatabaseModel = Field(default_factory=DatabaseModel)


# 全局配置实例
settings = GlobalSetting()

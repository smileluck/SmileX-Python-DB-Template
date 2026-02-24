"""
数据库URL构建器
提供灵活的数据库连接URL构建功能，支持MySQL和PostgreSQL
"""

from dataclasses import dataclass
from enum import Enum
from urllib.parse import quote_plus
from typing import Optional


class DatabaseType(str, Enum):
    """数据库类型枚举"""
    MYSQL = "mysql"
    PGSQL = "postgresql"


class DriverType(str, Enum):
    """驱动类型枚举"""
    SYNC = "sync"
    ASYNC = "async"


@dataclass
class DatabaseCredentials:
    """数据库凭证数据类"""
    username: str
    password: str
    host: str
    port: int
    database: str
    
    def __post_init__(self):
        """验证参数"""
        if not self.host:
            raise ValueError("数据库主机地址不能为空")
        if not self.database:
            raise ValueError("数据库名称不能为空")
        if not (1 <= self.port <= 65535):
            raise ValueError(f"数据库端口无效: {self.port}")


@dataclass
class DatabaseURLBuilder:
    """
    数据库URL构建器
    
    简化数据库连接URL的创建过程，支持多种数据库和驱动类型
    
    特性:
    - 自动URL编码处理
    - 支持同步/异步驱动
    - MySQL和PostgreSQL原生支持
    - 灵活的查询参数配置
    
    使用示例:
    ```python
    # MySQL同步连接
    builder = DatabaseURLBuilder(
        db_type=DatabaseType.MYSQL,
        credentials=DatabaseCredentials(
            username="root",
            password="password",
            host="localhost",
            port=3306,
            database="testdb"
        )
    )
    url = builder.build_sync_url()  # mysql+pymysql://...
    
    # PostgreSQL异步连接
    url = builder.build_async_url()  # postgresql+asyncpg://...
    
    # 带额外参数
    url = builder.build_url(
        driver_type=DriverType.ASYNC,
        query_params={"sslmode": "require"}
    )
    ```
    """
    
    db_type: DatabaseType
    credentials: DatabaseCredentials
    charset: str = "utf8mb4"
    encoding: str = "utf8"
    # application_name: str = "cloud-database"
    
    SYNC_DRIVERS = {
        DatabaseType.MYSQL: "pymysql",
        DatabaseType.PGSQL: "psycopg2",
    }
    
    ASYNC_DRIVERS = {
        DatabaseType.MYSQL: "aiomysql",
        DatabaseType.PGSQL: "asyncpg",
    }
    
    def get_sync_driver(self) -> str:
        """获取同步驱动名称"""
        return self.SYNC_DRIVERS.get(self.db_type, "pymysql")
    
    def get_async_driver(self) -> str:
        """获取异步驱动名称"""
        return self.ASYNC_DRIVERS.get(self.db_type, "asyncpg")
    
    def _encode_password(self, password: str) -> str:
        """URL编码密码"""
        return quote_plus(password)
    
    def _build_base_url(self, driver: str) -> str:
        """
        构建基础URL部分
        
        Args:
            driver: 驱动名称
            
        Returns:
            基础URL字符串
        """
        encoded_password = self._encode_password(self.credentials.password)
        
        if self.db_type == DatabaseType.MYSQL:
            return (
                f"mysql+{driver}://"
                f"{self.credentials.username}:{encoded_password}@"
                f"{self.credentials.host}:{self.credentials.port}/"
                f"{self.credentials.database}"
            )
        else:
            return (
                f"postgresql+{driver}://"
                f"{self.credentials.username}:{encoded_password}@"
                f"{self.credentials.host}:{self.credentials.port}/"
                f"{self.credentials.database}"
            )
    
    def _build_query_string(self, query_params: Optional[dict] = None) -> str:
        """
        构建查询参数字符串
        
        Args:
            query_params: 额外的查询参数字典
            
        Returns:
            查询参数字符串
        """
        params = {}
        
        if self.db_type == DatabaseType.MYSQL:
            params["charset"] = self.charset
        # else:
            # params["application_name"] = self.application_name
        
        if query_params:
            params.update(query_params)
        
        if not params:
            return ""
        
        query_parts = []
        for key, value in params.items():
            if value is not None:
                query_parts.append(f"{key}={quote_plus(str(value))}")
        
        return "?" + "&".join(query_parts)
    
    def build_sync_url(self, query_params: Optional[dict] = None) -> str:
        """
        构建同步数据库连接URL
        
        Args:
            query_params: 额外的查询参数字典
            
        Returns:
            完整的数据库连接URL
        """
        driver = self.get_sync_driver()
        base_url = self._build_base_url(driver)
        query_string = self._build_query_string(query_params)
        return base_url + query_string
    
    def build_async_url(self, query_params: Optional[dict] = None) -> str:
        """
        构建异步数据库连接URL
        
        Args:
            query_params: 额外的查询参数字典
            
        Returns:
            完整的数据库连接URL
        """
        driver = self.get_async_driver()
        base_url = self._build_base_url(driver)
        query_string = self._build_query_string(query_params)
        return base_url + query_string
    
    def build_url(
        self,
        driver_type: DriverType = DriverType.SYNC,
        query_params: Optional[dict] = None
    ) -> str:
        """
        构建数据库连接URL
        
        Args:
            driver_type: 驱动类型（同步/异步）
            query_params: 额外的查询参数字典
            
        Returns:
            完整的数据库连接URL
        """
        if driver_type == DriverType.ASYNC:
            return self.build_async_url(query_params)
        return self.build_sync_url(query_params)
    
    def build_mysql_url(
        self,
        async_mode: bool = False,
        query_params: Optional[dict] = None
    ) -> str:
        """
        构建MySQL连接URL（便捷方法）
        
        Args:
            async_mode: 是否使用异步驱动
            query_params: 额外的查询参数字典
            
        Returns:
            MySQL连接URL
        """
        return self.build_url(
            driver_type=DriverType.ASYNC if async_mode else DriverType.SYNC,
            query_params=query_params
        )
    
    def build_pgsql_url(
        self,
        async_mode: bool = False,
        query_params: Optional[dict] = None
    ) -> str:
        """
        构建PostgreSQL连接URL（便捷方法）
        
        Args:
            async_mode: 是否使用异步驱动
            query_params: 额外的查询参数字典
            
        Returns:
            PostgreSQL连接URL
        """
        return self.build_url(
            driver_type=DriverType.ASYNC if async_mode else DriverType.SYNC,
            query_params=query_params
        )
    
    @classmethod
    def from_connection_string(
        cls,
        connection_string: str,
        db_type: Optional[DatabaseType] = None
    ) -> "DatabaseURLBuilder":
        """
        从连接字符串创建URL构建器
        
        Args:
            connection_string: 完整连接字符串或部分连接信息
            db_type: 数据库类型，若可推断则可不传
            
        Returns:
            DatabaseURLBuilder实例
            
        Example:
            ```python
            # 从完整URL解析
            builder = DatabaseURLBuilder.from_connection_string(
                "mysql+pymysql://user:pass@localhost:3306/mydb"
            )
            
            # 从配置信息创建
            builder = DatabaseURLBuilder.from_connection_string(
                "host=localhost port=3306 dbname=test",
                db_type=DatabaseType.MYSQL
            )
            ```
        """
        if "://" in connection_string:
            return cls._parse_full_url(connection_string, db_type)
        return cls._parse_config_string(connection_string, db_type)
    
    @classmethod
    def _parse_full_url(
        cls,
        url: str,
        db_type: Optional[DatabaseType] = None
    ) -> "DatabaseURLBuilder":
        """解析完整URL"""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        
        if not db_type:
            if parsed.scheme.startswith("mysql"):
                db_type = DatabaseType.MYSQL
            elif parsed.scheme.startswith("postgresql"):
                db_type = DatabaseType.PGSQL
            else:
                raise ValueError(f"无法识别的数据库类型: {url}")
        
        return cls(
            db_type=db_type,
            credentials=DatabaseCredentials(
                username=parsed.username or "",
                password=parsed.password or "",
                host=parsed.hostname or "localhost",
                port=parsed.port or (3306 if db_type == DatabaseType.MYSQL else 5432),
                database=parsed.path.lstrip("/") or ""
            )
        )
    
    @classmethod
    def _parse_config_string(
        cls,
        config: str,
        db_type: Optional[DatabaseType] = None
    ) -> "DatabaseURLBuilder":
        """解析配置字符串"""
        parts = {}
        for part in config.split():
            if "=" in part:
                key, value = part.split("=", 1)
                parts[key] = value
        
        if not db_type:
            db_type = DatabaseType.MYSQL
        
        return cls(
            db_type=db_type,
            credentials=DatabaseCredentials(
                username=parts.get("user", ""),
                password=parts.get("password", ""),
                host=parts.get("host", "localhost"),
                port=int(parts.get("port", 3306 if db_type == DatabaseType.MYSQL else 5432)),
                database=parts.get("dbname", parts.get("database", ""))
            )
        )
    
    def __str__(self) -> str:
        """返回连接URL字符串"""
        return self.build_sync_url()
    
    def __repr__(self) -> str:
        """返回详细表示"""
        return (
            f"DatabaseURLBuilder("
            f"db_type={self.db_type.value}, "
            f"host={self.credentials.host}, "
            f"port={self.credentials.port}, "
            f"database={self.credentials.database})"
        )


def build_database_url(
    db_type: str,
    username: str,
    password: str,
    host: str,
    port: int,
    database: str,
    async_mode: bool = False,
    **kwargs
) -> str:
    """
    便捷函数：快速构建数据库连接URL
    
    Args:
        db_type: 数据库类型（mysql/postgresql）
        username: 用户名
        password: 密码
        host: 主机地址
        port: 端口
        database: 数据库名称
        async_mode: 是否使用异步驱动
        **kwargs: 额外参数
        
    Returns:
        数据库连接URL
        
    Example:
        ```python
        url = build_database_url(
            db_type="mysql",
            username="root",
            password="password",
            host="localhost",
            port=3306,
            database="mydb"
        )
        ```
    """
    db_type_enum = DatabaseType(db_type.lower())
    credentials = DatabaseCredentials(
        username=username,
        password=password,
        host=host,
        port=port,
        database=database
    )
    
    builder = DatabaseURLBuilder(
        db_type=db_type_enum,
        credentials=credentials,
        **kwargs
    )
    
    return builder.build_url(
        driver_type=DriverType.ASYNC if async_mode else DriverType.SYNC
    )

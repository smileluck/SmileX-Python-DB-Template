"""
基础模型类
提供所有模型共享的字段和方法
"""

from datetime import datetime
from typing import Annotated

from sqlalchemy import BigInteger, Boolean, Integer, DateTime, TypeDecorator
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    mapped_column,
    Mapped,
    MappedAsDataclass,
    declared_attr,
)
from sqlalchemy.sql import func
from database.utils.snowflake import snowflake
from sqlalchemy import select
from database.utils.timezone import timezone
from database.utils.str_utils import camel_to_snake

id_key = Annotated[
    int,
    mapped_column(
        BigInteger,
        primary_key=True,
        unique=True,
        index=True,
        autoincrement=True,
        sort_order=-999,
        comment="主键 ID",
    ),
]

snowflake_id_key = Annotated[
    int,
    mapped_column(
        BigInteger,
        primary_key=True,
        unique=True,
        index=True,
        default=snowflake.generate,
        sort_order=-999,
        comment="雪花算法主键 ID",
    ),
]


class UserMixin(MappedAsDataclass):
    """用户 Mixin 数据类"""

    created_by: Mapped[int] = mapped_column(sort_order=998, comment="创建者")
    updated_by: Mapped[int | None] = mapped_column(
        init=False, default=None, sort_order=998, comment="修改者"
    )


class DateTimeMixin(MappedAsDataclass):
    """日期 Mixin 数据类"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        init=False,
        default_factory=timezone.now,
        sort_order=999,
        comment="创建时间",
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        init=False,
        default=None,
        sort_order=999,
        onupdate=timezone.now,
        comment="更新时间",
    )
    
    # @property
    # def created_at_str(self) -> str:
    #     """格式化的创建时间字符串（如：2023-10-01 12:00:00）"""
    #     if self.created_at:
    #         # 转换时区后格式化（假设数据库存储UTC时间）
    #         local_time = self.created_at.astimezone(ZoneInfo("Asia/Shanghai"))
    #         return local_time.strftime("%Y-%m-%d %H:%M:%S")
    #     return ""

    # @property
    # def updated_at_str(self) -> str | None:
    #     """格式化的更新时间字符串"""
    #     if self.updated_at:
    #         local_time = self.updated_at.astimezone(ZoneInfo("Asia/Shanghai"))
    #         return local_time.strftime("%Y-%m-%d %H:%M:%S")
    #     return None


class LogicMixin(MappedAsDataclass):
    """逻辑 Mixin 数据类"""

    id: Mapped[snowflake_id_key] = mapped_column(init=False)

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        init=False,
        default=None,
        sort_order=997,
        comment="删除时间，为空则未删除",
    )

    def soft_delete(self):
        """逻辑删除当前记录"""
        self.deleted_at = timezone.now()


class MappedBase(AsyncAttrs, DeclarativeBase):
    """
    声明式基类, 作为所有基类或数据模型类的父类而存在

    `AsyncAttrs <https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncAttrs>`__

    `DeclarativeBase <https://docs.sqlalchemy.org/en/20/orm/declarative_config.html>`__

    `mapped_column() <https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column>`__
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """生成表名"""
        return camel_to_snake(cls.__name__)

    @declared_attr.directive
    def __table_args__(cls) -> dict:
        """表配置"""
        return {"comment": cls.__doc__ or ""}


class DataClassBase(MappedAsDataclass, MappedBase):
    """
    声明性数据类基类, 带有数据类集成, 允许使用更高级配置, 但你必须注意它的一些特性, 尤其是和 DeclarativeBase 一起使用时。
    例如，使用中间表时，可继承该类，不需要时间类等。

    `MappedAsDataclass <https://docs.sqlalchemy.org/en/20/orm/dataclasses.html#orm-declarative-native-dataclasses>`__
    """

    __abstract__ = True


class Base(DataClassBase, LogicMixin, DateTimeMixin):
    """
    声明性数据类基类, 带有数据类集成, 并包含 MiXin 数据类基础表结构
    """

    __abstract__ = True

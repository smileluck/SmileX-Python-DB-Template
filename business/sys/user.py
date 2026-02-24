from database.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, Table, Column
from typing import List, Optional
from datetime import datetime
from .association_tables import sys_user_role_association


class SysUser(Base):
    """
    系统用户表
    存储系统管理用户的基本信息和认证凭证
    """

    # 用户基本信息
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, comment="用户名"
    )

    password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码（加密存储）"
    )

    nickname: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="用户昵称"
    )

    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=True, comment="邮箱"
    )

    phone: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=True, comment="手机号"
    )

    avatar: Mapped[str] = mapped_column(Text, nullable=True, comment="头像URL")

    # 登录信息
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="最后登录时间"
    )

    last_login_ip: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="最后登录IP"
    )

    # 关联关系
    # 与角色表的多对多关系
    roles: Mapped[List["SysRole"]] = relationship(
        secondary=sys_user_role_association,
        back_populates="users",
        lazy="select",
    )

    # 状态信息
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="状态：True-启用，False-禁用"
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否为超级管理员"
    )

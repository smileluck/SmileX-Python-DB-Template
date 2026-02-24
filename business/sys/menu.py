from database.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Text, Boolean, ForeignKey, Enum
from typing import List, Optional
import enum
from .association_tables import sys_role_menu_association


class MenuType(enum.Enum):
    """
    菜单类型枚举
    """

    CATALOG = "catalog"  # 目录
    MENU = "menu"  # 菜单
    BUTTON = "button"  # 按钮
    EXTERNAL = "external"  # 外部链接


class SysMenu(Base):
    """
    系统菜单表
    存储系统菜单、目录和按钮等权限点
    """

    # 菜单层级结构
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_menu.id", ondelete="CASCADE"),
        nullable=True,
        comment="父菜单ID，顶级菜单为0或NULL",
    )

    # 菜单图标（没有默认值）
    icon: Mapped[str] = mapped_column(String(50), nullable=True, comment="菜单图标")

    # 菜单基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="菜单名称")

    path: Mapped[str] = mapped_column(String(255), nullable=True, comment="路由路径")

    component: Mapped[str] = mapped_column(
        String(255), nullable=True, comment="组件路径"
    )

    redirect: Mapped[str] = mapped_column(
        String(255), nullable=True, comment="重定向路径"
    )

    # 权限标识
    permission: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="权限标识，如 sys:user:list"
    )

    # 路由元信息
    meta_title: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="路由标题"
    )

    meta_icon: Mapped[str] = mapped_column(
        String(50), nullable=True, comment="路由图标"
    )

    # 关联关系
    # 与角色表的多对多关系
    roles: Mapped[List["SysRole"]] = relationship(
        secondary=sys_role_menu_association,
        back_populates="menus",
        lazy="select",
    )

    # 与自身的一对多关系（子菜单）
    children: Mapped[List["SysMenu"]] = relationship(
        back_populates="parent",
        lazy="select",
        cascade="all, delete-orphan",
    )

    # 与自身的多对一关系（父菜单）
    parent: Mapped["SysMenu"] = relationship(
        back_populates="children",
        remote_side="SysMenu.id",
        lazy="select",
    )

    meta_hidden: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否隐藏菜单"
    )

    meta_affix: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否固定标签"
    )

    meta_breadcrumb: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否显示面包屑"
    )

    # 状态信息
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="状态：True-启用，False-禁用"
    )

    # 菜单类型（有默认值）
    type: Mapped[MenuType] = mapped_column(
        Enum(MenuType),
        default=MenuType.MENU,
        comment="菜单类型：catalog-目录, menu-菜单, button-按钮, external-外部链接",
    )

    # 排序字段
    sort: Mapped[int] = mapped_column(default=0, comment="排序号")

from sqlalchemy import Column, ForeignKey, Table,String
from sqlalchemy.orm import Mapped, relationship
from database.models.base import Base

# 角色菜单关联表(重复定义是为了确保每个文件独立可用)
sys_role_menu_association = Table(
    "sys_role_menu",
    Base.metadata,
    Column("role_id", ForeignKey("sys_role.id", ondelete="CASCADE"), primary_key=True, comment="角色ID"),
    Column("menu_id", ForeignKey("sys_menu.id", ondelete="CASCADE"), primary_key=True, comment="菜单ID"),
    Column(
        "permission",
        String(255),
        nullable=False,
        default="read",
        comment="权限类型：read, write, delete等",
    ),
    comment="角色菜单关联表",
)

# 用户角色关联表(重复定义是为了确保每个文件独立可用)
sys_user_role_association = Table(
    "sys_user_role",
    Base.metadata,
    Column("user_id", ForeignKey("sys_user.id", ondelete="CASCADE"), primary_key=True, comment="用户ID"),
    Column("role_id", ForeignKey("sys_role.id", ondelete="CASCADE"), primary_key=True, comment="角色ID"),
    comment="用户角色关联表",
)

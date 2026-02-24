from database.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Text, Boolean


class SysPermission(Base):
    """
    系统权限表
    存储细粒度的权限点，用于精确的权限控制
    """
    # 权限基本信息
    name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False, 
        comment="权限名称"
    )
    
    code: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        index=True, 
        nullable=False, 
        comment="权限编码（唯一标识符）"
    )
    
    description: Mapped[str] = mapped_column(
        Text, 
        nullable=True, 
        comment="权限描述"
    )
    
    # 资源路径
    resource_path: Mapped[str] = mapped_column(
        String(255), 
        nullable=True, 
        comment="资源路径（如API路径、菜单URL等）"
    )
    
    # 请求方法
    method: Mapped[str] = mapped_column(
        String(10), 
        nullable=True, 
        comment="请求方法（如GET, POST, PUT, DELETE等）"
    )
    
    # 权限分类
    category: Mapped[str] = mapped_column(
        String(50), 
        nullable=True, 
        comment="权限分类"
    )
    
    # 权限类型
    type: Mapped[str] = mapped_column(
        String(20), 
        default="api", 
        comment="权限类型：api, menu, button, data等"
    )
    
    
    # 状态信息
    status: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        comment="状态：True-启用，False-禁用"
    )
    
    # 排序字段
    sort: Mapped[int] = mapped_column(
        default=0, 
        comment="排序号"
    )
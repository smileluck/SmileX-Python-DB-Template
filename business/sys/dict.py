from database.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Text, Boolean, ForeignKey
from typing import List


class SysDict(Base):
    """
    系统字典表
    存储字典分类信息
    """

    # 字典名称
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="字典名称")

    # 字典编码，唯一标识符
    code: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False, comment="字典编码"
    )

    # 字典描述
    description: Mapped[str] = mapped_column(Text, nullable=True, comment="字典描述")

    # 关联关系
    # 与字典数据表的一对多关系
    dict_items: Mapped[List["SysDictItem"]] = relationship(
        back_populates="dict", lazy="select"
    )
    
    # 是否启用
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="状态：True-启用，False-禁用"
    )

    # 是否为系统内置字典
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否为系统内置字典"
    )

    # 排序字段
    sort: Mapped[int] = mapped_column(default=0, comment="排序号")



class SysDictItem(Base):
    """
    系统字典数据表
    存储字典的具体数据项
    """

    # 关联字典ID
    dict_id: Mapped[int] = mapped_column(
        ForeignKey("sys_dict.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联字典ID，字典删除时级联删除",
    )

    # 字典项键值
    value: Mapped[str] = mapped_column(String(100), nullable=False, comment="字典项值")

    # 字典项文本
    label: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="字典项文本"
    )

    # 字典项描述
    description: Mapped[str] = mapped_column(Text, nullable=True, comment="字典项描述")

    # 扩展信息(JSON格式)
    ext_info: Mapped[str] = mapped_column(
        Text, nullable=True, comment="扩展信息(JSON格式)"
    )

    # 关联关系
    # 与字典表的多对一关系
    dict: Mapped["SysDict"] = relationship(back_populates="dict_items", lazy="select")

    # 是否启用
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="状态：True-启用，False-禁用"
    )

    # 排序字段
    sort: Mapped[int] = mapped_column(default=0, comment="排序号")


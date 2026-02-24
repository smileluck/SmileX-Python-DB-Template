from database.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Text, Boolean, Enum
import enum


class ConfigType(enum.Enum):
    """
    系统配置类型枚举
    """

    STRING = "string"  # 字符串类型
    NUMBER = "number"  # 数字类型
    BOOLEAN = "boolean"  # 布尔类型
    JSON = "json"  # JSON类型
    ARRAY = "array"  # 数组类型


class ConfigGroup(enum.Enum):
    """
    系统配置分组枚举
    """

    SYSTEM = "system"  # 系统配置
    SECURITY = "security"  # 安全配置
    LOG = "log"  # 日志配置
    NETWORK = "network"  # 网络配置
    STORAGE = "storage"  # 存储配置
    CUSTOM = "custom"  # 自定义配置


class SysConfig(Base):
    """
    系统配置表
    存储系统全局配置参数
    """

    # 配置键名，唯一标识符
    key: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False, comment="配置键名"
    )

    # 配置值
    value: Mapped[str] = mapped_column(String(255), nullable=False, comment="配置值")

    # 默认值
    default_value: Mapped[str] = mapped_column(
        String(255), nullable=True, comment="默认值"
    )

    # 校验规则
    validation_rule: Mapped[str] = mapped_column(
        String(255), nullable=True, comment="校验规则"
    )
    # 配置描述
    description: Mapped[str] = mapped_column(
        String(255), nullable=True, comment="配置描述"
    )

    # 配置类型
    type: Mapped[ConfigType] = mapped_column(
        Enum(ConfigType), default=ConfigType.STRING, comment="配置类型"
    )

    # 配置分组
    group: Mapped[ConfigGroup] = mapped_column(
        Enum(ConfigGroup), default=ConfigGroup.SYSTEM, comment="配置分组"
    )

    # 是否可编辑
    editable: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否可编辑")

    # 是否为系统内置配置
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否为系统内置配置"
    )

    # 是否必填
    required: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否必填")

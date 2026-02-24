from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import sys
import io,os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# config.set_main_option("sqlalchemy.url", database_url)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None
from database.models.base import Base  # 导入你的模型基类

target_metadata = Base.metadata
import os
import importlib

# 自动扫描并导入所有模型模块
def auto_import_models():
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    # 模型所在的根目录（根据实际项目结构调整）

    # 需要扫描的目录
    include_dirs = ["business"]

    # 排除不需要扫描的目录（可选）
    exclude_dirs = ["__pycache__", "tests"]

    for include_dir in include_dirs:
        models_root_dir = os.path.join(PROJECT_ROOT, include_dir)
        if os.path.exists(models_root_dir):
            # 递归扫描所有Python文件
            for root, dirs, files in os.walk(models_root_dir):
                # 过滤排除目录
                dirs[:] = [d for d in dirs if d not in exclude_dirs]

                for file in files:
                    # 只处理.py文件，且排除__init__.py
                    if file.endswith(".py") and not file.startswith("__"):
                        # 构造模块的相对路径
                        relative_path = os.path.relpath(root, PROJECT_ROOT)
                        module_name = (
                            relative_path.replace(os.sep, ".") + "." + file[:-3]
                        )

                        try:
                            # 动态导入模块（导入后模型会自动注册到Base.metadata）
                            importlib.import_module(module_name)
                            # 可选：打印导入的模块名，方便调试
                            print(f"已自动导入模型模块: {module_name}")
                        except ImportError as e:
                            # 非致命错误：打印警告但不中断程序
                            print(f"警告: 无法导入模型模块 {module_name}，错误: {e}")

# 执行自动导入
auto_import_models()

print("已识别的表：", target_metadata.tables.keys())

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        encoding="utf-8",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

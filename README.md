# SmileX Python DB Template 


SmileX Python 数据库模板项目，一个基于 SQLAlchemy 2.0 和 Alembic 构建的现代化异步数据库管理解决方案。本项目可作为 Python 项目的数据库基础设施模板，支持快速集成 PostgreSQL 和 MySQL 数据库。

## 项目简介

本项目是一个**通用的 Python 数据库模板**，旨在为各类 Python 项目提供开箱即用的数据库基础设施。通过 Git Submodule 或直接复制的方式，可以快速将数据库管理能力集成到新项目中，避免重复搭建数据库层代码。

### 核心价值

- **快速启动**：无需从零搭建数据库层，直接集成即可使用
- **最佳实践**：遵循 SQLAlchemy 2.0 最新规范，代码质量有保障
- **灵活扩展**：模块化设计，可根据业务需求自由扩展
- **生产就绪**：包含完整的迁移管理、连接池配置等生产级特性

## 项目特性

- **异步数据库操作**：基于 SQLAlchemy 2.0 异步支持，高并发场景性能优异
- **同步/异步双模式**：同时支持同步和异步数据库操作，适应不同场景需求
- **自动模型发现**：启动时自动扫描并注册所有数据模型
- **双环境配置**：独立配置测试和生产环境的数据库迁移
- **多数据库支持**：通过插件机制支持 PostgreSQL、MySQL 等
- **类型安全**：完整的类型提示支持，IDE 智能提示友好
- **Alembic 迁移**：完整的数据库版本管理和迁移支持

## 环境要求

- Python 3.13+
- PostgreSQL 13+ 或 MySQL 8.0+
- uv 包管理器（推荐）或 pip

## 快速安装

### 1. 创建虚拟环境

```bash
# 使用 uv（推荐）
uv venv
.venv\Scripts\activate

# 或使用 pip
python -m venv .venv
.venv\Scripts\activate
```

### 2. 安装依赖

```bash
# 使用 uv
uv pip install -e .

# 或使用 pip
pip install -e .
```

## 作为 Submodule 集成到其他项目

### 1. 添加 Submodule

在目标项目中执行以下命令，将 SmileX-Python-DB-Template 作为 submodule 添加：

```bash
# 进入目标项目根目录
cd /path/to/your/project

# 添加 submodule，默认会放在当前目录下的 SmileX-Python-DB-Template 文件夹中
git submodule add https://github.com/smileluck/SmileX-Python-DB-Template.git SmileX-Python-DB-Template

# 如果需要指定不同的文件夹名称
git submodule add https://github.com/smileluck/SmileX-Python-DB-Template.git <custom-folder-name>
```

### 2. 初始化和更新 Submodule

克隆包含 submodule 的项目时，需要初始化 submodule：

```bash
# 克隆主项目
# 方法1：直接克隆时初始化 submodule
git clone --recursive <main-repo-url>

# 方法2：先克隆主项目，再初始化 submodule
git clone <main-repo-url>
cd <main-repo-folder>

# 初始化并更新所有 submodule
git submodule update --init --recursive
```

### 3. 更新 Submodule

当 SmileX-Python-DB-Template 项目有更新时，在主项目中执行以下命令更新 submodule：

```bash
# 进入 submodule 目录
cd SmileX-Python-DB-Template

# 更新到最新版本
git pull origin main

# 或在主项目根目录执行
git submodule update --remote SmileX-Python-DB-Template

# 更新所有 submodule
git submodule update --remote
```

### 4. 在主项目中使用

#### 安装 submodule 作为依赖

```bash
# 在主项目中安装 submodule
# 使用 uv
uv pip install -e ./SmileX-Python-DB-Template

# 或使用 pip
pip install -e ./SmileX-Python-DB-Template
```

#### 导入和使用

```python
# 导入数据库组件
from database import init_async_pool, get_session, AsyncDatabaseManager, DatabaseModel
from sqlalchemy import select

# 方式一：使用全局初始化函数
async def main():
    # 初始化数据库连接池
    settings = DatabaseModel(
        type="postgresql",
        host="127.0.0.1",
        port=5432,
        username="postgres",
        password="postgres",
        database="smilex_db",
    )
    await init_async_pool(settings)
    
    # 使用会话查询数据
    async for session in get_session():
        result = await session.execute(select(YourModel).where(YourModel.id == 1))
        data = result.scalar_one_or_none()

# 方式二：使用管理器实例
async def with_manager():
    manager = AsyncDatabaseManager()
    await manager.init_pool(settings)
    
    async with manager.get_session() as session:
        # 执行数据库操作
        pass
```

#### 执行数据库迁移

在主项目中执行 SmileX-Python-DB-Template 的迁移命令：

```bash
# 测试环境迁移
cd SmileX-Python-DB-Template
alembic upgrade head

# 或直接指定配置文件路径
cd /path/to/main/project
alembic -c SmileX-Python-DB-Template/alembic.ini upgrade head

# 生产环境迁移
alembic -c SmileX-Python-DB-Template/alembic_prod.ini upgrade head
```

### 5. Submodule 管理最佳实践

1. **定期更新 submodule**：确保主项目使用的是最新稳定版本的 submodule
2. **锁定特定版本**：在生产环境中，建议锁定 submodule 到特定 commit，避免意外更新
   ```bash
   # 进入 submodule 目录
   cd SmileX-Python-DB-Template
   
   # 切换到特定 commit
   git checkout <commit-hash>
   
   # 返回主项目并提交锁定状态
   cd ..
   git add SmileX-Python-DB-Template
   git commit -m "锁定 SmileX-Python-DB-Template 到特定版本"
   ```
3. **处理 submodule 冲突**：当主项目和 submodule 同时修改时，需要先解决 submodule 内部冲突，再更新主项目引用
4. **文档化依赖关系**：在主项目的 README 中说明 submodule 的用途和版本要求

### 6. 常见问题

#### Q1: submodule 更新后，主项目如何提交变更？

```bash
# 更新 submodule 后，主项目会检测到 submodule 引用变化
git status
# 输出示例：modified:   SmileX-Python-DB-Template (new commits)

# 提交 submodule 引用变更
git add SmileX-Python-DB-Template
git commit -m "更新 SmileX-Python-DB-Template submodule"
```

#### Q2: 如何移除 submodule？

```bash
# 1. 删除 .gitmodules 文件中的对应条目
# 2. 删除 .git/config 中的对应条目
# 3. 删除 submodule 目录
git rm --cached SmileX-Python-DB-Template
rm -rf SmileX-Python-DB-Template
# 4. 提交变更
git commit -m "移除 SmileX-Python-DB-Template submodule"
```

## 数据库配置

### 环境变量配置（推荐）

创建 `.env` 文件配置数据库连接：

```bash
# 数据库配置
DATABASE_HOST=127.0.0.1
DATABASE_PORT=5432
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=postgres
DATABASE_NAME=smilex_db
```

### 手动配置数据库URL

编辑 `alembic.ini`（测试环境）或 `alembic_prod.ini`（生产环境，如不存在，请复制`alembic.ini`）：

```ini
# alembic.ini
sqlalchemy.url = postgresql://postgres:postgres@127.0.0.1:5432/smilex_db

# alembic_prod.ini
sqlalchemy.url = postgresql://postgres:postgres@127.0.0.1:5432/smilex_db
```

## Alembic 数据库迁移

### 基本命令

#### 1. 查看当前迁移状态

```bash
# 测试环境
alembic current

# 生产环境
alembic -c alembic_prod.ini current
```

#### 2. 生成新迁移文件

当模型发生变更时，自动生成迁移脚本：

```bash
# 自动检测变更并生成迁移（测试环境）
alembic revision --autogenerate -m "描述变更内容"

# 生产环境
alembic -c alembic_prod.ini revision --autogenerate -m "描述变更内容"
```

**注意**：生成迁移文件后，请仔细检查文件内容，确保迁移逻辑正确。

#### 3. 执行迁移

```bash
# 升级到最新版本（测试环境）
alembic upgrade head

# 升级到指定版本（测试环境）
alembic upgrade +2  # 升级2个版本
alembic upgrade abc123  # 升级到特定revision

# 生产环境
alembic -c alembic_prod.ini upgrade head
```

#### 4. 回滚迁移

```bash
# 回滚一个版本（测试环境）
alembic downgrade -1

# 回滚到指定版本（测试环境）
alembic downgrade abc123

# 清空所有数据并重新创建（危险操作）
alembic downgrade base

# 生产环境
alembic -c alembic_prod.ini downgrade -1
```

#### 5. 查看迁移历史

```bash
# 查看完整迁移历史（测试环境）
alembic history

# 查看简洁版历史
alembic history --verbose

# 查看从指定版本开始的历史
alembic history --start:abc123

# 生产环境
alembic -c alembic_prod.ini history
```

#### 6. 标记迁移状态

手动标记迁移为已完成或取消：

```bash
# 标记迁移为已应用（测试环境）
alembic stamp abc123

# 生产环境
alembic -c alembic_prod.ini stamp abc123
```

### 完整部署流程

#### 测试环境部署

```bash
# 1. 确保虚拟环境已激活
.venv\Scripts\activate

# 2. 检查当前迁移状态
alembic current

# 3. 生成新迁移（如果有模型变更）
alembic revision --autogenerate -m "新增功能描述"

# 4. 执行迁移
alembic upgrade head

# 5. 验证迁移结果
alembic history
```

#### 生产环境部署

**重要**：生产环境部署前，请务必执行以下步骤：

```bash
# 1. 备份数据库（强烈建议）
pg_dump -h your_host -U your_user -d your_database > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 在测试环境验证迁移
alembic upgrade head  # 确保测试环境通过

# 3. 检查迁移脚本
alembic show abc123  # 查看指定迁移详情

# 4. 执行生产环境迁移
alembic -c alembic_prod.ini upgrade head

# 5. 验证生产环境迁移状态
alembic -c alembic_prod.ini current

# 6. 回滚计划（如有问题）
alembic -c alembic_prod.ini downgrade -1
```

#### 灰度发布建议

```bash
# 生产环境灰度发布流程
# 1. 先在测试环境完成全部迁移
alembic upgrade head

# 2. 检查迁移脚本无破坏性操作
alembic show <revision>

# 3. 备份生产数据库
pg_dump -h prod_host -U prod_user -d prod_db > backup.sql

# 4. 执行生产环境迁移
alembic -c alembic_prod.ini upgrade head

# 5. 监控应用运行状态
# 6. 如有问题，执行回滚
alembic -c alembic_prod.ini downgrade -1
```

### 离线迁移

在没有数据库连接的情况下生成迁移脚本：

```bash
# 生成SQL脚本（测试环境）
alembic upgrade --sql > migration_test.sql

# 生成SQL脚本（生产环境）
alembic -c alembic_prod.ini upgrade --sql > migration_prod.sql

# 执行SQL脚本
psql -h host -U user -d database -f migration_test.sql
```

### 迁移冲突解决

当多个分支合并时可能出现迁移冲突：

```bash
# 查看冲突位置
alembic heads

# 合并迁移
alembic merge -m "合并分支" abc123 def456
```

## 项目结构

```
SmileX-Python-DB-Template/
├── alembic/                       # Alembic 迁移配置
│   ├── versions/                  # 迁移脚本目录
│   ├── env.py                     # 迁移环境配置
│   └── script.py.mako             # 迁移脚本模板
├── alembic.ini                    # 数据库迁移配置
├── alembic_prod.ini               # 生产环境迁移配置
├── business/                      # 业务模型层（示例）
│   └── sys/                       # 系统管理模型
│       ├── user.py                # 用户模型
│       ├── role.py                # 角色模型
│       ├── permission.py          # 权限模型
│       ├── menu.py                # 菜单模型
│       ├── config.py              # 配置模型
│       ├── dict.py                # 字典模型
│       └── association_tables.py  # 关联表定义
├── database/                      # 数据库核心层
│   ├── manager/                   # 数据库管理器
│   │   ├── async_manager.py       # 异步连接池管理
│   │   └── sync_manager.py        # 同步连接池管理
│   ├── models/                    # 基础模型
│   │   ├── base.py                # 模型基类定义
│   │   └── dataclasses.py         # 数据类定义
│   ├── plugins/                   # 数据库插件
│   │   └── setup_database.py      # 数据库初始化插件
│   ├── utils/                     # 工具函数
│   │   ├── snowflake.py           # 雪花ID生成器
│   │   ├── str_utils.py           # 字符串工具
│   │   ├── timezone.py            # 时区处理
│   │   └── url_builder.py         # 数据库URL构建器
│   ├── __init__.py                # 模块导出
│   └── config.py                  # 配置管理
├── main.py                        # 使用示例入口
├── pyproject.toml                 # 项目配置
└── uv.lock                        # 依赖锁定文件
```

## 数据模型（示例）

> 以下为项目中包含的示例业务模型，您可以根据实际需求修改或替换。

### 系统管理模块

- **SysUser**：用户管理
- **SysRole**：角色管理
- **SysPermission**：权限管理
- **SysMenu**：菜单管理
- **SysConfig**：系统配置
- **SysDict**：数据字典

### 自定义模型

您可以轻松创建自己的数据模型：

```python
from database import Base, snowflake_id_key, DateTimeMixin
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column


class YourModel(Base, DateTimeMixin):
    """自定义数据模型示例"""
    __tablename__ = "your_table"
    
    id: Mapped[int] = snowflake_id_key()
    name: Mapped[str] = mapped_column(String(100), comment="名称")
    description: Mapped[str | None] = mapped_column(Text, comment="描述")
```

## 常见问题

### Q1: 迁移失败怎么办？

1. 检查数据库连接是否正常
2. 查看错误日志确认失败原因
3. 如果是语法问题，手动修复迁移文件
4. 必要时回滚到前一版本

### Q2: 如何重置测试数据库？

```bash
# 回滚所有迁移
alembic downgrade base

# 重新执行所有迁移
alembic upgrade head
```

### Q3: 迁移文件命名规则？

默认格式：`<revision>_<slug>.py`

- `revision`：8位哈希值
- `slug`：用户指定的描述（转换为slug格式）

### Q4: 如何跳过某个迁移？

```bash
# 标记迁移为已应用但不实际执行
alembic stamp abc123
```

## 注意事项

1. **生产环境操作前务必备份数据库**
2. **重要变更先在测试环境验证**
3. **迁移脚本需要代码审查**
4. **灰度发布降低风险**
5. **保留回滚能力**

## 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证开源。

```
Copyright 2024 SmileX

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
#   S m i l e X - P y t h o n - D B - T e m p l a t e 
 
 
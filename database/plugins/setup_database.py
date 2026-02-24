from sqlalchemy import Column, DateTime, func, event
from sqlalchemy.orm import (
    declarative_base,
    Session,
    with_loader_criteria,
)  # 导入 Session
from ..models.base import LogicMixin


def setup_soft_delete_plug() -> None:
    # 注册事件监听：拦截查询并添加过滤条件
    @event.listens_for(Session, "do_orm_execute")
    def _add_filtering_deleted_at(execute_state):
        """
        自动过滤掉被软删除的数据。
        deleted_at不为null即为被软删除。
        使用以下方法可以获得被软删除的数据。
        select(...).execution_options(include_deleted=True)
        """
        if (
            execute_state.is_select
            and not execute_state.is_column_load
            and not execute_state.is_relationship_load
            and not execute_state.execution_options.get("include_deleted", False)
        ):
            execute_state.statement = execute_state.statement.options(
                with_loader_criteria(
                    LogicMixin,
                    lambda cls: cls.deleted_at.is_(
                        None
                    ),  # deleted_at列为空则为未被软删除
                    include_aliases=True,
                )
            )

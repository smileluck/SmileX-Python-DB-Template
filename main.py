import os
import sys
import asyncio
import logging


from sqlalchemy import select


from business.sys.user import SysUser
from database import (
    init_async_pool,
    SyncDatabaseManager,
    DatabaseModel,
    Base,
    get_session,
)


logging.basicConfig(level=logging.INFO)


async def async_example():
    settings = DatabaseModel(
        type="postgresql",
        host="127.0.0.1",
        port=5432,
        username="postgres",
        password="postgres",
        database="smilex_db",
        pool_size=10,
        max_overflow=20,
    )

    await init_async_pool(settings)

    async for session in get_session():
        result = await session.execute(select(SysUser).where(SysUser.id == 1))
        user = result.scalar_one_or_none()
        logging.info(f"User name {user.name}")


if __name__ == "__main__":
    asyncio.run(async_example())

#!/usr/bin/env python3
"""为已存在的数据库补充 user_configs.use_custom_llm 列（幂等）。

背景：use_custom_llm 是后加的列，`Base.metadata.create_all` 只建表不补列，
新装的库由 init.sql / create_all 自带该列，老库需执行本脚本一次。

用法:
    .venv/Scripts/python.exe scripts/migrate_use_custom_llm.py
"""

import asyncio
import sys
from pathlib import Path

# 修复 Windows 控制台 GBK 编码无法输出 emoji 的问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from daa.settings import get_settings


async def migrate() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)

    async with engine.connect() as conn:
        # 查询列是否存在
        result = await conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = :db AND table_name = 'user_configs' "
                "AND column_name = 'use_custom_llm'"
            ),
            {"db": settings.MYSQL_DATABASE},
        )
        exists = result.scalar_one()

        if exists:
            print("✅ use_custom_llm 列已存在，无需迁移")
            return

        await conn.execute(
            text(
                "ALTER TABLE user_configs "
                "ADD COLUMN use_custom_llm BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )
        await conn.commit()
    print("✅ 已为 user_configs 添加 use_custom_llm 列（默认 FALSE）")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())

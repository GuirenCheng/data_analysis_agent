#!/usr/bin/env python3
"""数据库初始化脚本 — 创建所有表并运行 Alembic 迁移。

用法:
    python scripts/init_db.py
"""

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).parent.parent))

from daa.models.base import Base
from daa.settings import get_settings
from sqlalchemy import create_engine


def init_database():
    """创建所有 ORM 表。"""
    settings = get_settings()

    print(f"🔧 连接到 MySQL: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    print(f"📦 数据库: {settings.MYSQL_DATABASE}")

    engine = create_engine(settings.database_url_sync, echo=True)

    # 创建所有表
    print("🏗️  创建数据库表...")
    Base.metadata.create_all(engine)

    print("✅ 数据库初始化完成！")
    print("\n已创建以下表:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")


if __name__ == "__main__":
    init_database()

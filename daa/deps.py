"""FastAPI 依赖注入 — 汇聚常用依赖。"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from daa.db.session import get_db
from daa.middleware.auth import get_current_user, get_optional_user

# 重新导出，方便 API 层引用
__all__ = [
    "get_db",
    "get_current_user",
    "get_optional_user",
]

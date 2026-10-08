"""SQLAlchemy 声明式基类和通用 Mixin。"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。"""
    pass


class UUIDMixin:
    """UUID 主键 Mixin。"""

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )


class TimestampMixin:
    """创建/更新时间戳 Mixin。

    注意：``default`` / ``onupdate`` 使用 Python 端的 ``datetime.now``，
    而非 SQL 表达式 ``func.now()``。否则在异步 SQLAlchemy 下 INSERT 后
    该列会处于 expired 状态，访问时触发 lazy-load，在 pydantic 校验
    （同步上下文）中报 ``MissingGreenlet``。
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        server_default=func.now(),
    )

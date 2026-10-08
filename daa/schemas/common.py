"""通用 Pydantic 模型 — 分页、错误响应等。"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页查询参数。"""

    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    per_page: int = Field(default=20, ge=1, le=100, description="每页数量")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型。"""

    items: list[T] = Field(default_factory=list)
    total: int = Field(default=0)
    page: int = Field(default=1)
    per_page: int = Field(default=20)


class ErrorResponse(BaseModel):
    """标准错误响应。"""

    detail: str
    code: str = "internal_error"
    timestamp: datetime = Field(default_factory=datetime.now)


class StatusResponse(BaseModel):
    """通用状态响应。"""

    status: str
    message: str = ""


class DeletedResponse(BaseModel):
    """删除操作响应。"""

    deleted: bool = True
    id: str

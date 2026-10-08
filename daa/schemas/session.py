"""分析会话相关 Pydantic schemas。"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from daa.schemas.analysis import AnalysisStepOut, FigureOut

SessionStatus = Literal["pending", "running", "completed", "failed", "cancelled"]


class SessionCreate(BaseModel):
    """创建分析会话请求。"""

    query: str = Field(..., min_length=1, max_length=10000, description="自然语言分析需求")
    file_ids: list[str] = Field(default_factory=list, description="关联的上传文件 ID 列表")
    max_rounds: int = Field(default=20, ge=5, le=50, description="最大分析轮次")


class SessionOut(BaseModel):
    """分析会话详情响应。"""

    id: str
    user_id: str
    title: Optional[str] = None
    query: str
    status: SessionStatus = "pending"
    max_rounds: int = 20
    current_round: int = 0
    progress: float = 0.0
    error_message: Optional[str] = None
    output_dir: Optional[str] = None
    report_path: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionDetailOut(SessionOut):
    """会话详情（含步骤和图表）。"""

    steps: list[AnalysisStepOut] = Field(default_factory=list)
    figures: list[FigureOut] = Field(default_factory=list)


class SessionListOut(BaseModel):
    """会话列表响应。"""

    items: list[SessionOut] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    per_page: int = 20

"""分析相关 Pydantic schemas。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnalysisStepOut(BaseModel):
    """分析步骤响应。"""

    id: str
    round_number: int
    action: str
    code: Optional[str] = None
    execution_output: Optional[str] = None
    execution_error: Optional[str] = None
    execution_success: Optional[bool] = None
    figures_collected: Optional[list[dict]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FigureOut(BaseModel):
    """图表信息。"""

    figure_number: Optional[int] = None
    filename: str = ""
    file_path: str = ""
    description: str = ""
    analysis: str = ""


class ReportOut(BaseModel):
    """分析报告响应。"""

    markdown: str = ""
    figures: list[FigureOut] = Field(default_factory=list)
    report_file_path: Optional[str] = None


class AnalysisCreateResponse(BaseModel):
    """创建分析任务的响应。"""

    id: str
    status: str = "pending"
    message: str = "分析任务已创建，正在排队处理"


class StreamProgressEvent(BaseModel):
    """SSE 进度事件。"""

    status: str  # pending | running | completed | failed | cancelled
    progress: float = 0.0  # 0.0 - 1.0
    current_round: int = 0
    message: str = ""

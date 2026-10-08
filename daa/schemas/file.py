"""文件相关 Pydantic schemas。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FileOut(BaseModel):
    """上传文件响应。"""

    id: str
    original_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    columns_detected: Optional[list[str]] = None
    row_count: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FilePreviewOut(BaseModel):
    """文件预览响应。"""

    columns: list[str] = Field(default_factory=list)
    rows: list[list] = Field(default_factory=list)
    total_rows: int = 0


class FileUploadResponse(BaseModel):
    """文件上传成功响应。"""

    file: FileOut
    message: str = "文件上传成功"

"""上传文件模型。"""

from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from daa.models.base import UUIDMixin, TimestampMixin, Base


class AnalysisFile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "analysis_files"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("analysis_sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    original_name: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128))
    columns_detected: Mapped[Optional[dict]] = mapped_column(JSON)
    row_count: Mapped[Optional[int]] = mapped_column(Integer)

    # 关系
    user = relationship("User", back_populates="files")
    session = relationship("AnalysisSession", back_populates="files")

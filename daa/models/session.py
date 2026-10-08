"""分析会话模型。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from daa.models.base import UUIDMixin, TimestampMixin, Base


class AnalysisSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "analysis_sessions"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(512))
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )  # pending | running | completed | failed | cancelled
    max_rounds: Mapped[int] = mapped_column(Integer, default=20)
    current_round: Mapped[int] = mapped_column(Integer, default=0)
    output_dir: Mapped[Optional[str]] = mapped_column(String(1024))
    report_path: Mapped[Optional[str]] = mapped_column(String(1024))
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 关系
    user = relationship("User", back_populates="sessions")
    steps = relationship(
        "AnalysisStep", back_populates="session", lazy="dynamic", cascade="all, delete-orphan"
    )
    files = relationship(
        "AnalysisFile", back_populates="session", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<AnalysisSession(id={self.id}, status={self.status})>"

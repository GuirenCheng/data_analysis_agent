"""分析步骤模型 — 记录每次 LLM 交互的详细信息。"""

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from daa.models.base import UUIDMixin, TimestampMixin, Base


class AnalysisStep(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "analysis_steps"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(MEDIUMTEXT)
    response_text: Mapped[Optional[str]] = mapped_column(MEDIUMTEXT)
    execution_output: Mapped[Optional[str]] = mapped_column(Text)
    execution_error: Mapped[Optional[str]] = mapped_column(Text)
    execution_success: Mapped[Optional[bool]] = mapped_column(Boolean)
    figures_collected: Mapped[Optional[dict]] = mapped_column(JSON)

    # 关系
    session = relationship("AnalysisSession", back_populates="steps")

    def __repr__(self) -> str:
        return f"<AnalysisStep(session={self.session_id}, round={self.round_number}, action={self.action})>"

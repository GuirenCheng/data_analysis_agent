"""用户配置模型。"""

from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from daa.models.base import UUIDMixin, TimestampMixin, Base


class UserConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_configs"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    llm_provider: Mapped[str] = mapped_column(String(64), default="openai")
    llm_model: Mapped[str] = mapped_column(String(128), default="gpt-4-turbo-preview")
    llm_base_url: Mapped[Optional[str]] = mapped_column(String(512))
    llm_api_key_encrypted: Mapped[Optional[str]] = mapped_column(String(512))
    temperature: Mapped[float] = mapped_column(Float, default=0.1)
    max_tokens: Mapped[int] = mapped_column(Integer, default=16384)
    default_max_rounds: Mapped[int] = mapped_column(Integer, default=20)
    default_output_dir: Mapped[str] = mapped_column(String(512), default="outputs")

    # 关系
    user = relationship("User", back_populates="config")

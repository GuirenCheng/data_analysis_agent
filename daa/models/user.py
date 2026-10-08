"""用户模型。"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from daa.models.base import UUIDMixin, TimestampMixin, Base


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系
    sessions = relationship("AnalysisSession", back_populates="user", lazy="dynamic")
    files = relationship("AnalysisFile", back_populates="user", lazy="dynamic")
    config = relationship("UserConfig", back_populates="user", uselist=False, lazy="joined")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"

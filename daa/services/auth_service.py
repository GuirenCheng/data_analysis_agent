"""认证服务 — JWT 创建/验证、密码哈希、用户注册/登录。"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from daa.models.user import User
from daa.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码。"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, expires_minutes: Optional[int] = None) -> str:
    """创建 JWT access token。"""
    settings = get_settings()
    expire = datetime.now() + timedelta(
        minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES
    )
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(),
        "type": "access",
    }
    return jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> Optional[str]:
    """解码 JWT token，返回 user_id 或 None。"""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        return user_id
    except JWTError:
        return None


async def register_user(
    db: AsyncSession, username: str, email: str, password: str
) -> User:
    """注册新用户。"""
    # 检查用户名/邮箱是否已存在
    existing = await db.execute(
        select(User).where((User.username == username) | (User.email == email))
    )
    if existing.scalar_one_or_none():
        raise ValueError("用户名或邮箱已被注册")

    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    """验证用户凭据，返回用户或 None。"""
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user

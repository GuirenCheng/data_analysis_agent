"""JWT 认证中间件 — FastAPI 依赖注入。"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from daa.db.session import get_db
from daa.models.user import User
from daa.services.auth_service import decode_access_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT token 提取当前用户。

    支持两种携带方式：``Authorization: Bearer <token>`` 请求头，或
    ``?token=<token>`` 查询参数（用于浏览器原生 EventSource 无法设置
    请求头的场景，如 SSE 进度流）。

    用法:
        @app.get("/me")
        async def me(user: User = Depends(get_current_user)):
            return {"username": user.username}
    """
    token = credentials.credentials if credentials else None
    if not token:
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """可选认证 — 不强制要求 token。"""
    if not credentials:
        return None

    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        return None

    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    return result.scalar_one_or_none()

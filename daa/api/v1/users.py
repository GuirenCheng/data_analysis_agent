"""用户 API。"""

from fastapi import APIRouter, Depends

from daa.middleware.auth import get_current_user
from daa.models.user import User
from daa.schemas.auth import UserOut

router = APIRouter(prefix="/users")


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    """获取当前登录用户信息。"""
    return UserOut.model_validate(user)

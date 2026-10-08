"""用户配置 API。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from daa.db.session import get_db
from daa.middleware.auth import get_current_user
from daa.models.user import User
from daa.schemas.config import UserConfigOut, UserConfigUpdate
from daa.services.config_service import get_user_config, update_user_config

router = APIRouter(prefix="/configs")


@router.get("/me", response_model=UserConfigOut)
async def get_my_config(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的 LLM 配置。"""
    config = await get_user_config(db, user.id)
    return UserConfigOut.model_validate(config)


@router.put("/me", response_model=UserConfigOut)
async def update_my_config(
    request: UserConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户的 LLM 配置。"""
    config = await update_user_config(
        db, user.id, **request.model_dump(exclude_none=True)
    )
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    await db.commit()
    return UserConfigOut.model_validate(config)

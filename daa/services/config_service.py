"""配置服务 — 用户 LLM 配置管理。"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from daa.models.user_config import UserConfig


async def get_user_config(db: AsyncSession, user_id: str) -> UserConfig:
    """获取用户配置，如果不存在则创建默认配置。"""
    result = await db.execute(
        select(UserConfig).where(UserConfig.user_id == user_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        config = UserConfig(
            id=str(uuid.uuid4()),
            user_id=user_id,
        )
        db.add(config)
        await db.flush()

    return config


async def update_user_config(
    db: AsyncSession, user_id: str, **kwargs
) -> Optional[UserConfig]:
    """部分更新用户配置。"""
    config = await get_user_config(db, user_id)
    if not config:
        return None

    allowed_fields = {
        "llm_provider",
        "llm_model",
        "llm_base_url",
        "llm_api_key_encrypted",
        "temperature",
        "max_tokens",
        "default_max_rounds",
        "default_output_dir",
    }

    for key, value in kwargs.items():
        if key == "llm_api_key" and value:
            config.llm_api_key_encrypted = value  # 生产环境中应加密
        elif key in allowed_fields and value is not None:
            setattr(config, key, value)

    await db.flush()
    return config

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
        "use_custom_llm",
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


async def get_user_llm_overrides(
    db: AsyncSession, user_id: str
) -> Optional[dict]:
    """读取用户的自定义 LLM 配置，用于在分析任务中覆盖全局默认。

    仅在用户显式启用「自定义模型配置」时返回覆盖字典；否则返回 None，
    此时分析流程回退到 .env 里的全局 LLM 配置。
    """
    result = await db.execute(
        select(UserConfig).where(UserConfig.user_id == user_id)
    )
    config = result.scalar_one_or_none()
    if not config or not config.use_custom_llm:
        return None

    return {
        "model": config.llm_model or "",
        "base_url": config.llm_base_url or "",
        "api_key": config.llm_api_key_encrypted or "",
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }

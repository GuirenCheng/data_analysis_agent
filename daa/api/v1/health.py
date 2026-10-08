"""健康检查 API。"""

import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from daa.db.redis import get_redis
from daa.db.session import get_db
from daa.settings import get_settings

router = APIRouter(prefix="/health")

_start_time = time.time()


@router.get("")
async def health_check():
    """基础健康检查。"""
    settings = get_settings()
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "uptime": round(time.time() - _start_time, 2),
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """就绪检查 — 验证所有依赖服务是否可用。"""
    checks = {
        "database": False,
        "redis": False,
    }

    # 检查 MySQL
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass

    # 检查 Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = True
    except Exception:
        pass

    all_ready = all(checks.values())

    return {
        "status": "ready" if all_ready else "not_ready",
        **checks,
    }

"""Redis 客户端管理 — 缓存和任务队列基础设施。"""

import json
from typing import Any, Callable, Optional

import redis.asyncio as aioredis
from arq.connections import ArqRedis, RedisSettings, create_pool

from daa.settings import get_settings

_redis: Optional[aioredis.Redis] = None
_arq_redis: Optional[ArqRedis] = None


async def get_redis() -> aioredis.Redis:
    """获取 Redis 异步客户端（懒加载单例）。

    用法:
        redis = await get_redis()
        await redis.get("key")
    """
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    return _redis


async def get_arq_redis() -> ArqRedis:
    """获取 ARQ 任务队列 Redis 客户端（懒加载单例）。

    用于在 API 层将后台分析任务入队。
    """
    global _arq_redis
    if _arq_redis is None:
        settings = get_settings()
        redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        _arq_redis = await create_pool(redis_settings)
    return _arq_redis


async def close_redis() -> None:
    """关闭所有 Redis 连接。"""
    global _redis, _arq_redis
    if _redis:
        await _redis.close()
        _redis = None
    if _arq_redis:
        await _arq_redis.close()
        _arq_redis = None


class RedisCache:
    """异步 Redis 缓存工具类。

    提供缓存读取模式 (cache-aside) 和常用的 Redis 操作。
    """

    def __init__(self, redis_client: aioredis.Redis | None = None):
        self._redis = redis_client

    async def _get_client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: int = 300,
    ) -> Any:
        """缓存读取模式：先查 Redis，未命中则调用 factory 并缓存。

        Args:
            key: 缓存键
            factory: 异步或同步工厂函数
            ttl: 缓存过期时间（秒）
        """
        client = await self._get_client()
        cached = await client.get(key)
        if cached is not None:
            return json.loads(cached)

        value = await factory() if hasattr(factory, "__await__") else factory()
        await client.setex(key, ttl, json.dumps(value, default=str))
        return value

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        client = await self._get_client()
        await client.setex(key, ttl, json.dumps(value, default=str))

    async def get(self, key: str) -> Optional[Any]:
        client = await self._get_client()
        cached = await client.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def delete(self, key: str) -> None:
        client = await self._get_client()
        await client.delete(key)

    async def exists(self, key: str) -> bool:
        client = await self._get_client()
        return bool(await client.exists(key))

    async def invalidate_pattern(self, pattern: str) -> int:
        """删除所有匹配 pattern 的键。"""
        client = await self._get_client()
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await client.delete(*keys)
        return 0


# 全局缓存实例
cache = RedisCache()

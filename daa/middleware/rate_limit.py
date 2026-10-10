"""速率限制中间件。"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from daa.db.redis import get_redis
from daa.settings import get_settings


async def rate_limit_middleware(request: Request, call_next):
    """简单的滑动窗口速率限制（基于 IP）。

    对 /health 和 /docs 等路径不做限制。
    """
    # 跳过不需要限流的路径
    path = request.url.path
    if path.startswith(("/health", "/docs", "/openapi.json", "/redoc")):
        return await call_next(request)

    settings = get_settings()

    # Redis 不可用时放行（fail-open），避免限流组件把整个服务拖垮为 500。
    try:
        redis = await get_redis()
    except Exception:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}"

    try:
        current = await redis.get(key)
        if current is None:
            await redis.setex(key, 60, 1)
        elif int(current) >= settings.RATE_LIMIT_PER_MINUTE:
            # 直接返回 429 响应。在 BaseHTTPMiddleware 里 raise HTTPException
            # 会被外层 ServerErrorMiddleware 当成 500 处理，导致前端看到 500。
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "请求过于频繁，请稍后再试"},
            )
        else:
            await redis.incr(key)
    except Exception:
        # Redis 读写异常时同样放行，保证业务请求不受限流组件影响
        pass

    return await call_next(request)

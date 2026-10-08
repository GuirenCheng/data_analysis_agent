"""请求日志中间件。"""

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """记录每个 HTTP 请求的耗时和状态码。"""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start_time = time.time()
        response = await call_next(request)
        elapsed = time.time() - start_time

        # 简洁的控制台日志
        method = request.method
        path = request.url.path
        status = response.status_code

        print(f"[{request_id}] {method} {path} → {status} ({elapsed:.3f}s)")

        response.headers["X-Request-ID"] = request_id
        return response

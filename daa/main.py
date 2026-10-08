"""FastAPI 应用入口 — 应用工厂和生命周期管理。"""

import sys

# 修复 Windows 控制台 GBK 编码无法输出 emoji 的问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from contextlib import asynccontextmanager

from fastapi import FastAPI

from daa.api.v1.router import api_v1_router
from daa.db.session import close_db
from daa.db.redis import close_redis
from daa.middleware.cors import setup_cors
from daa.middleware.logging import RequestLoggingMiddleware
from daa.middleware.rate_limit import rate_limit_middleware
from daa.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化，关闭时清理。"""
    settings = get_settings()
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    print(f"📡 LLM: {settings.LLM_MODEL} @ {settings.LLM_BASE_URL}")
    print(f"🗄️  MySQL: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    print(f"📦 Redis: {settings.REDIS_URL}")

    yield  # 应用运行中

    # 清理
    print("🛑 正在关闭...")
    await close_redis()
    await close_db()
    print("✅ 已关闭所有连接")


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。"""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="企业级 LLM 驱动的智能数据分析代理",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── 中间件 ─────────────────────────
    setup_cors(app)
    app.add_middleware(RequestLoggingMiddleware)
    app.middleware("http")(rate_limit_middleware)

    # ── 路由 ───────────────────────────
    app.include_router(api_v1_router)

    return app


# 应用实例（uvicorn 入口）
app = create_app()

"""API v1 路由聚合。"""

from fastapi import APIRouter

from daa.api.v1.auth import router as auth_router
from daa.api.v1.users import router as users_router
from daa.api.v1.sessions import router as sessions_router
from daa.api.v1.analyses import router as analyses_router
from daa.api.v1.files import router as files_router
from daa.api.v1.configs import router as configs_router
from daa.api.v1.rag import router as rag_router
from daa.api.v1.health import router as health_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router, tags=["认证"])
api_v1_router.include_router(users_router, tags=["用户"])
api_v1_router.include_router(sessions_router, tags=["会话"])
api_v1_router.include_router(analyses_router, tags=["分析"])
api_v1_router.include_router(files_router, tags=["文件"])
api_v1_router.include_router(configs_router, tags=["配置"])
api_v1_router.include_router(rag_router, tags=["RAG"])
api_v1_router.include_router(health_router, tags=["健康检查"])

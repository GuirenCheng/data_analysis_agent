"""CORS 配置。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    """配置 CORS 中间件。"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

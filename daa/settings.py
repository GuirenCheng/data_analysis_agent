"""应用配置管理 — 使用 pydantic-settings 从环境变量加载所有配置。"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置，所有值从 .env 文件和环境变量加载。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── 应用 ──────────────────────────────────
    APP_NAME: str = "Data Analysis Agent"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # ── 数据库 (MySQL) ────────────────────────
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "daa"
    MYSQL_PASSWORD: str = "daa_password"
    MYSQL_DATABASE: str = "data_analysis_agent"
    MYSQL_ECHO: bool = False

    @property
    def database_url(self) -> str:
        return (
            f"mysql+asyncmy://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"mysql+mysqldb://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    # ── Redis ─────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── ChromaDB (向量数据库) ──────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # ── LLM 配置 ──────────────────────────────
    LLM_PROVIDER: str = "openai"  # openai | openai_compatible | anthropic
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4-turbo-preview"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 16384

    # 备用 LLM (内容过滤错误时切换)
    LLM_FALLBACK_API_KEY: Optional[str] = None
    LLM_FALLBACK_BASE_URL: Optional[str] = None
    LLM_FALLBACK_MODEL: Optional[str] = None

    # ── JWT ───────────────────────────────────
    JWT_SECRET_KEY: str = "jwt-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ── 文件存储 ──────────────────────────────
    DEFAULT_OUTPUT_DIR: str = "outputs"
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_UPLOAD_EXTENSIONS: str = ".csv,.xlsx,.xls,.json,.parquet"

    # ── 分析配置 ──────────────────────────────
    DEFAULT_MAX_ROUNDS: int = 20
    MAX_CODE_EXECUTION_TIMEOUT: int = 120  # 秒

    # ── 速率限制 ──────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 30

    # ── RAG ───────────────────────────────────
    RAG_CHUNK_SIZE: int = 800
    RAG_CHUNK_OVERLAP: int = 100
    RAG_TOP_K: int = 5
    # 检索到历史内容的余弦相似度阈值，低于此值的片段会被丢弃（防止无关上下文诱发幻觉）
    RAG_SIMILARITY_THRESHOLD: float = 0.3

    # ── Embedding（RAG 嵌入向量）──────────────────
    # DeepSeek 不提供 embedding 接口，需单独配置一个 OpenAI 兼容的 embedding 服务
    # （如硅基流动/智谱/OpenAI）。留空则回退到 LLM_API_KEY / LLM_BASE_URL。
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_BASE_URL: Optional[str] = None
    EMBEDDING_MODEL: str = "BAAI/bge-m3"


@lru_cache()
def get_settings() -> Settings:
    """单例 Settings 实例，整个应用共享。"""
    return Settings()

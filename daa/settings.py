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
    # 0.5 = 50%：低于 50% 相似度的召回一律丢弃（硬过滤，减少无关内容）
    RAG_SIMILARITY_THRESHOLD: float = 0.5

    # ── Embedding（RAG 嵌入向量）──────────────────
    # DeepSeek 不提供 embedding 接口，需单独配置一个 OpenAI 兼容的 embedding 服务
    # （如硅基流动/智谱/OpenAI）。留空则回退到 LLM_API_KEY / LLM_BASE_URL。
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_BASE_URL: Optional[str] = None
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    # bge 系列为「query vs 文档」检索训练，查询侧需加指令前缀以更好对齐；
    # 留空则不加（仅用于文档侧，不加指令）。
    EMBEDDING_QUERY_INSTRUCTION: str = (
        "Represent this sentence for searching relevant passages: "
    )

    # ── Rerank（RAG 检索后二次精排）──────────────────
    # 稠密向量的余弦相似度基线偏高（无关内容也 0.6+），单靠阈值无法区分相关/无关；
    # 用交叉编码器 reranker 对候选重新打分，能真正拉开差距。
    RERANK_ENABLED: bool = True
    RERANK_MODEL: str = "BAAI/bge-reranker-v2-m3"
    # 留空则回退到 EMBEDDING_API_KEY / EMBEDDING_BASE_URL（SiliconFlow 同一套）
    RERANK_API_KEY: Optional[str] = None
    RERANK_BASE_URL: Optional[str] = None
    # rerank 相关性分数阈值：低于此值的候选被丢弃（交叉编码器分数比余弦可靠得多）
    RERANK_THRESHOLD: float = 0.3
    # 每个内容类型召回的候选数（rerank 前，越多召回越全、rerank 成本越高）
    RERANK_CANDIDATE_N: int = 30

    # ── 混合检索（稠密向量 + 词法召回）──────────────────
    # 稠密召回有语义天花板：跨语言（中文 query vs 英文代码）、罕见词、字面重叠
    # 等情况，余弦相似度会失准。词法召回用查询分词后做子串匹配（近似 BM25），
    # 把「字面命中」的文档也捞进候选池，最终交给 reranker 精排（天然融合器）。
    HYBRID_RETRIEVAL_ENABLED: bool = True
    # 每个关键词、每个内容类型最多召回多少条词法命中（子串匹配本身无分数，超出的截断）
    LEXICAL_RECALL_K: int = 20
    # 词法召回的关键词上限（分词后按词长降序取前 N 个，长词区分度更高）
    LEXICAL_MAX_KEYWORDS: int = 8
    # rerank 前候选池总量上限（稠密召回优先保留，词法命中补到上限）
    RERANK_MAX_CANDIDATES: int = 200


@lru_cache()
def get_settings() -> Settings:
    """单例 Settings 实例，整个应用共享。"""
    return Settings()

"""文本嵌入器 — 使用 OpenAI 兼容的 embedding API 生成向量。"""

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from daa.settings import get_settings


class EmbeddingUnavailableError(RuntimeError):
    """向量嵌入服务不可用（连接失败等），用于区分「没搜到」与「搜不了」。"""


class Embedder:
    """文本嵌入器封装。

    使用 OpenAI 兼容的 embedding API 生成文本向量。

    注意：DeepSeek 不提供 embedding 接口，需在 .env 里单独配置
    EMBEDDING_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL；
    这三项留空时回退到 LLM_API_KEY / LLM_BASE_URL。
    """

    def __init__(self):
        self._embeddings = self._build_embeddings()

    def _build_embeddings(self):
        settings = get_settings()
        api_key = settings.EMBEDDING_API_KEY or settings.LLM_API_KEY
        base_url = settings.EMBEDDING_BASE_URL or settings.LLM_BASE_URL
        return OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=api_key,
            base_url=base_url,
        )

    def embed_text(self, text: str) -> list[float]:
        """生成单个文本的嵌入向量。

        首次失败时重建底层 OpenAI 客户端重试一次，以自愈 keep-alive
        连接被服务端关闭导致的偶发 ``Connection error``。
        """
        try:
            return self._embeddings.embed_query(text)
        except Exception as first_error:
            try:
                self._embeddings = self._build_embeddings()
                return self._embeddings.embed_query(text)
            except Exception:
                raise EmbeddingUnavailableError(str(first_error)) from first_error

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量生成嵌入向量。"""
        try:
            return self._embeddings.embed_documents(texts)
        except Exception as first_error:
            try:
                self._embeddings = self._build_embeddings()
                return self._embeddings.embed_documents(texts)
            except Exception:
                raise EmbeddingUnavailableError(str(first_error)) from first_error


@lru_cache()
def get_embedder() -> Embedder:
    """返回进程级共享的 Embedder 单例，避免每次请求重建 OpenAIEmbeddings。"""
    return Embedder()

"""文本嵌入器 — 使用 OpenAI 兼容的 embedding API 生成向量。"""

from langchain_openai import OpenAIEmbeddings

from daa.settings import get_settings


class Embedder:
    """文本嵌入器封装。

    使用 OpenAI 兼容的 embedding API 生成文本向量。

    注意：DeepSeek 不提供 embedding 接口，需在 .env 里单独配置
    EMBEDDING_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL；
    这三项留空时回退到 LLM_API_KEY / LLM_BASE_URL。
    """

    def __init__(self):
        settings = get_settings()
        api_key = settings.EMBEDDING_API_KEY or settings.LLM_API_KEY
        base_url = settings.EMBEDDING_BASE_URL or settings.LLM_BASE_URL
        self._embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=api_key,
            base_url=base_url,
        )

    def embed_text(self, text: str) -> list[float]:
        """生成单个文本的嵌入向量。"""
        return self._embeddings.embed_query(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量生成嵌入向量。"""
        return self._embeddings.embed_documents(texts)

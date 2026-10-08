"""RAG 检索器 — 语义搜索历史分析内容。"""

from dataclasses import dataclass, field
from typing import Optional

from daa.rag.embedder import Embedder
from daa.settings import get_settings


@dataclass
class RAGContext:
    """RAG 检索结果项。"""

    content_text: str
    content_type: str = ""
    source_session_id: str = ""
    similarity: float = 0.0
    metadata: dict = field(default_factory=dict)


class RAGRetriever:
    """语义检索器。

    使用当前查询的嵌入向量搜索 ChromaDB，
    返回最相似的历史分析内容作为上下文。
    """

    def __init__(self, chroma_client=None):
        self._chroma_client = chroma_client
        self._embedder: Optional[Embedder] = None
        # 键名须与 indexer 写入的 content_type 元数据一致（query/code/report/figure_caption）
        self._collections: dict[str, str] = {
            "query": "analysis_queries",
            "code": "analysis_code",
            "report": "analysis_reports",
            "figure_caption": "analysis_figures",
        }

    def _get_embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = Embedder()
        return self._embedder

    async def _get_chroma(self):
        """懒加载 ChromaDB 客户端。"""
        if self._chroma_client is None:
            try:
                import chromadb
                from daa.settings import get_settings
                settings = get_settings()
                self._chroma_client = chromadb.PersistentClient(
                    path=settings.CHROMA_PERSIST_DIR
                )
            except Exception:
                return None
        return self._chroma_client

    async def retrieve_context(
        self,
        user_id: str,
        current_query: str,
        top_k: int = 5,
        content_types: Optional[list[str]] = None,
    ) -> list[RAGContext]:
        """检索与当前查询最相关的历史分析内容。

        Args:
            user_id: 用户 ID（限制范围）
            current_query: 当前查询文本
            top_k: 每类返回的最大结果数
            content_types: 要搜索的内容类型，默认为全部

        Returns:
            按相似度降序排列的上下文列表
        """
        client = await self._get_chroma()
        if client is None:
            return []

        embedder = self._get_embedder()
        try:
            query_embedding = embedder.embed_text(current_query)
        except Exception as e:
            print(
                f"⚠️ 查询嵌入失败（请检查 EMBEDDING_API_KEY/BASE_URL，"
                f"DeepSeek 无 embedding 接口）: {e}"
            )
            return []

        threshold = get_settings().RAG_SIMILARITY_THRESHOLD

        types_to_search = content_types or list(self._collections.keys())
        all_results: list[RAGContext] = []

        for content_type in types_to_search:
            collection_name = self._collections.get(content_type)
            if not collection_name:
                continue

            try:
                collection = client.get_collection(collection_name)
            except Exception:
                continue

            try:
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where={"user_id": user_id},
                    include=["documents", "metadatas", "distances"],
                )
            except Exception:
                continue

            if not results["ids"] or not results["ids"][0]:
                continue

            for i, doc_id in enumerate(results["ids"][0]):
                doc_text = results["documents"][0][i] if results["documents"] and results["documents"][0] else ""
                metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {}
                distance = results["distances"][0][i] if results["distances"] and results["distances"][0] else 1.0

                # 距离转相似度 (cosine distance → similarity)
                similarity = max(0.0, 1.0 - float(distance))

                # 丢弃低于阈值的无关片段，避免无关历史内容诱发幻觉
                if similarity < threshold:
                    continue

                all_results.append(RAGContext(
                    content_text=doc_text,
                    content_type=content_type,
                    source_session_id=metadata.get("source_session_id", ""),
                    similarity=round(similarity, 4),
                    metadata=metadata,
                ))

        # 按相似度降序排列
        all_results.sort(key=lambda x: x.similarity, reverse=True)
        return all_results[:top_k]


def format_rag_context_for_prompt(contexts: list[RAGContext]) -> str:
    """将 RAG 检索结果格式化为提示词中的参考上下文。

    Args:
        contexts: RAGContext 列表

    Returns:
        格式化的字符串，可直接注入 system prompt
    """
    if not contexts:
        return "（无相关历史分析参考）"

    parts = ["📚 **相关历史分析参考**:"]
    for i, ctx in enumerate(contexts[:5], 1):
        parts.append(f"\n{i}. [{ctx.content_type}] 相似度: {ctx.similarity}")
        # 截断过长文本
        text = ctx.content_text[:600]
        if ctx.content_type == "code":
            parts.append(f"```python\n{text}\n```")
        else:
            parts.append(text)
    return "\n".join(parts)

"""RAG 检索器 — 混合检索（稠密向量 + 词法召回）搜索历史分析内容。

检索流程：
    query → 路A 稠密召回（bge-m3 向量 → 余弦 top-N）
          → 路B 词法召回（jieba 分词 → 子串匹配，近似 BM25）
          → 合并去重 → reranker 精排（天然融合器，无需 RRF）→ 阈值过滤 → top-k

为什么要混合：
    稠密召回有语义天花板——跨语言（中文 query vs 英文代码）、罕见词、字面重叠等
    情况下余弦相似度会失准，导致「字面命中的文档」排不进来（如「鸢尾花」明明在
    报告里，稠密却把它排到英文代码之后）。词法召回把「字面命中」的文档直接捞进
    候选池，最终由 reranker 用交叉编码器统一打分，两条路自然融合。
"""

import re
from dataclasses import dataclass, field
from typing import Optional

try:
    import jieba
    _HAS_JIEBA = True
except ImportError:  # pragma: no cover — jieba 是声明依赖，此分支仅防御
    _HAS_JIEBA = False

from daa.rag.chroma import get_chroma_client
from daa.rag.embedder import Embedder, EmbeddingUnavailableError, get_embedder
from daa.settings import get_settings


@dataclass
class RAGContext:
    """RAG 检索结果项。"""

    content_text: str
    content_type: str = ""
    source_session_id: str = ""
    similarity: float = 0.0
    metadata: dict = field(default_factory=dict)
    doc_id: str = ""  # ChromaDB 文档 ID，用于稠密/词法两条路去重


# 词法召回时过滤掉的停用词（英文功能词 + 中文功能词/疑问词）。
# 这些词高频且无区分度，做成子串匹配只会捞回一堆无关文档。
_STOPWORDS = {
    # 英文功能词
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "how", "what", "why", "which", "who", "when", "where", "to", "of", "in",
    "on", "for", "with", "and", "or", "not", "can", "could", "should",
    "would", "do", "does", "did", "i", "you", "we", "they", "it", "this",
    "that", "these", "those", "get", "got", "use", "using", "used", "find",
    "want", "need", "please", "me", "my", "have", "has", "had", "into",
    "from", "by", "at", "as", "if", "so", "no", "yes", "there", "here",
    # 中文功能词/疑问词
    "如何", "怎么", "怎样", "什么", "为什么", "哪些", "哪里", "一个", "一下",
    "这个", "那个", "以及", "并且", "或者", "还是", "可以", "能够", "需要",
    "应该", "的", "了", "是", "在", "有", "和", "与", "及", "或", "等",
    "我", "你", "他", "她", "它", "我们", "你们", "他们", "吗", "呢", "吧",
}


def _extract_keywords(query: str, max_keywords: int = 8) -> list[str]:
    """从查询中提取词法召回用的关键词（中英文混合）。

    - 英文/数字：按非字母数字切词；
    - 中文：jieba 分词，只保留含中文的词；
    - 过滤停用词、单字词，去重后按词长降序取前 max_keywords 个（长词区分度更高）。
    """
    tokens: list[str] = re.findall(r"[A-Za-z][A-Za-z0-9_]*", query)
    if _HAS_JIEBA and re.search(r"[一-鿿]", query):
        for w in jieba.lcut(query):
            w = w.strip()
            if re.search(r"[一-鿿]", w):
                tokens.append(w)

    seen: set[str] = set()
    keywords: list[str] = []
    for t in tokens:
        t = t.strip().lower()
        if len(t) < 2 or t in _STOPWORDS or t in seen:
            continue
        seen.add(t)
        keywords.append(t)

    # 长词优先（区分度更高），再截断
    keywords.sort(key=len, reverse=True)
    return keywords[:max_keywords]


class RAGRetriever:
    """混合检索器（稠密向量 + 词法召回 + reranker 精排）。"""

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
            self._embedder = get_embedder()
        return self._embedder

    async def _get_chroma(self):
        """懒加载 ChromaDB 客户端（进程级单例）。"""
        if self._chroma_client is None:
            try:
                self._chroma_client = get_chroma_client()
            except Exception:
                return None
        return self._chroma_client

    def _lexical_recall(
        self,
        client,
        user_id: str,
        keywords: list[str],
        types_to_search: list[str],
        lexical_k: int,
    ) -> list[RAGContext]:
        """词法召回（BM25 近似）：对每个关键词做子串匹配，捞取字面命中的文档。

        只负责「把字面命中的文档捞进候选池」，不做最终排序——最终相关性交给
        reranker。此处按「命中的关键词占比」给一个粗分数，供 rerank 关闭/失败
        时的回退路径使用（含全部关键词的文档分数更高）。
        """
        # doc_id -> [RAGContext, 命中的关键词数]
        matched: dict[str, list] = {}
        for content_type in types_to_search:
            collection_name = self._collections.get(content_type)
            if not collection_name:
                continue
            try:
                collection = client.get_collection(collection_name)
            except Exception:
                continue
            for kw in keywords:
                try:
                    res = collection.get(
                        where={"user_id": user_id},
                        where_document={"$contains": kw},
                        limit=lexical_k,
                        include=["documents", "metadatas"],
                    )
                except Exception:
                    continue
                ids = res.get("ids") or []
                docs = res.get("documents") or []
                metas = res.get("metadatas") or []
                for j, doc_id in enumerate(ids):
                    entry = matched.get(doc_id)
                    if entry is None:
                        meta = metas[j] if j < len(metas) else {}
                        ctx = RAGContext(
                            content_text=docs[j] if j < len(docs) else "",
                            content_type=content_type,
                            source_session_id=meta.get("source_session_id", ""),
                            similarity=0.0,
                            metadata=meta,
                            doc_id=doc_id,
                        )
                        matched[doc_id] = [ctx, 1]
                    else:
                        entry[1] += 1

        hits: list[RAGContext] = []
        for ctx, cnt in matched.values():
            ctx.similarity = round(cnt / len(keywords), 4)
            hits.append(ctx)
        hits.sort(key=lambda x: x.similarity, reverse=True)
        return hits

    async def retrieve_context(
        self,
        user_id: str,
        current_query: str,
        top_k: int = 5,
        content_types: Optional[list[str]] = None,
    ) -> list[RAGContext]:
        """检索与当前查询最相关的历史分析内容（混合检索）。

        Args:
            user_id: 用户 ID（限制范围）
            current_query: 当前查询文本
            top_k: 最终返回的最大结果数
            content_types: 要搜索的内容类型，默认为全部

        Returns:
            按相关性降序排列的上下文列表
        """
        client = await self._get_chroma()
        if client is None:
            return []

        embedder = self._get_embedder()
        try:
            # 查询侧加 bge 指令前缀，与文档侧向量正确对齐
            query_embedding = embedder.embed_query(current_query)
        except EmbeddingUnavailableError:
            # 嵌入服务不可用：向上抛出，让搜索 API 返回明确错误而非静默空结果
            raise
        except Exception as e:
            print(
                f"⚠️ 查询嵌入失败（请检查 EMBEDDING_API_KEY/BASE_URL，"
                f"DeepSeek 无 embedding 接口）: {e}"
            )
            return []

        settings = get_settings()
        threshold = settings.RAG_SIMILARITY_THRESHOLD
        rerank_candidate_n = settings.RERANK_CANDIDATE_N

        types_to_search = content_types or list(self._collections.keys())

        # 每个 collection 的召回数。关键：召回后**不要**按余弦全局/分类型截断到
        # top-N，否则小集合（如报告，可能只有十几条）里真正相关的内容会被余弦
        # 排名挤出去，出现「全部搜不到、限定单一类型才搜得到」的现象。全部交给
        # reranker 精排，让它自行挑出相关的。
        recall_k = max(top_k, rerank_candidate_n)

        # ── 路 A：稠密召回（语义）──
        dense_results: list[RAGContext] = []

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
                    n_results=recall_k,
                    where={"user_id": user_id},
                    include=["documents", "metadatas", "distances"],
                )
            except Exception:
                continue

            if not results["ids"] or not results["ids"][0]:
                continue

            for i in range(len(results["ids"][0])):
                doc_text = results["documents"][0][i] if results["documents"] and results["documents"][0] else ""
                metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {}
                distance = results["distances"][0][i] if results["distances"] and results["distances"][0] else 1.0

                # 距离转相似度 (cosine distance → similarity)
                similarity = max(0.0, 1.0 - float(distance))

                # 余弦阶段先不过滤，交给 rerank 精排（余弦基线偏高，硬阈值误杀严重）
                dense_results.append(RAGContext(
                    content_text=doc_text,
                    content_type=content_type,
                    source_session_id=metadata.get("source_session_id", ""),
                    similarity=round(similarity, 4),
                    metadata=metadata,
                    doc_id=results["ids"][0][i],
                ))

        # ── 路 B：词法召回（字面命中，近似 BM25）──
        lexical_hits: list[RAGContext] = []
        if settings.HYBRID_RETRIEVAL_ENABLED:
            keywords = _extract_keywords(current_query, settings.LEXICAL_MAX_KEYWORDS)
            if keywords:
                lexical_hits = self._lexical_recall(
                    client, user_id, keywords, types_to_search, settings.LEXICAL_RECALL_K
                )

        # ── 合并去重：稠密优先，词法补充；同一文档保留更高分 ──
        merged: dict[str, RAGContext] = {}
        for ctx in dense_results + lexical_hits:
            key = ctx.doc_id or ctx.content_text
            existing = merged.get(key)
            if existing is None:
                merged[key] = ctx
            elif ctx.similarity > existing.similarity:
                merged[key] = ctx
        all_results = list(merged.values())

        # 候选池总量上限（稠密召回优先保留，超出的词法尾部被截断）
        if len(all_results) > settings.RERANK_MAX_CANDIDATES:
            all_results = all_results[: settings.RERANK_MAX_CANDIDATES]

        # 按相似度降序（供 rerank 关闭/失败时的回退排序）
        all_results.sort(key=lambda x: x.similarity, reverse=True)

        # 二次精排：把所有召回的候选都交给 reranker（不截断），并按相关性分数阈值过滤
        if settings.RERANK_ENABLED and all_results:
            from daa.rag.reranker import rerank

            scores = await rerank(current_query, [c.content_text for c in all_results])
            if scores is not None:
                scored = [
                    (ctx, s) for ctx, s in zip(all_results, scores)
                    if s >= settings.RERANK_THRESHOLD
                ]
                scored.sort(key=lambda x: x[1], reverse=True)
                for ctx, s in scored[:top_k]:
                    ctx.similarity = round(s, 4)  # 用 rerank 分数替换余弦/词法分
                return [ctx for ctx, _ in scored[:top_k]]

        # 回退：rerank 关闭/失败时，用相似度（余弦或词法命中占比）+ 硬阈值
        filtered = [c for c in all_results if c.similarity >= threshold]
        return filtered[:top_k]


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

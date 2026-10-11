"""RAG 重排序器 — 用交叉编码器 reranker 对检索候选二次打分。

背景：稠密向量的余弦相似度基线偏高（bge-m3 对无关内容也会给出 0.6+ 的
相似度），单靠固定阈值无法区分相关与无关。交叉编码器（cross-encoder）把
「query 与文档」拼在一起做深度交互打分，能真正拉开相关/无关的差距，且
分数可直接当作可信的相关性阈值使用。
"""

from typing import Optional

import httpx

from daa.settings import get_settings


async def rerank(query: str, documents: list[str]) -> Optional[list[float]]:
    """对候选文档重新打分，返回与 ``documents`` 等长的相关性分数列表。

    调用 OpenAI 兼容的 rerank 接口（默认 SiliconFlow 的
    ``POST {base_url}/rerank``，模型 ``BAAI/bge-reranker-v2-m3``）。

    Args:
        query: 查询文本
        documents: 候选文档列表

    Returns:
        与 ``documents`` 等长的 ``relevance_score`` 列表（越相关越接近 1）；
        若未启用或调用失败，返回 ``None``，由调用方回退到余弦相似度。
    """
    if not documents:
        return []

    settings = get_settings()
    if not settings.RERANK_ENABLED:
        return None

    base_url = (
        settings.RERANK_BASE_URL
        or settings.EMBEDDING_BASE_URL
        or settings.LLM_BASE_URL
    ).rstrip("/")
    api_key = (
        settings.RERANK_API_KEY
        or settings.EMBEDDING_API_KEY
        or settings.LLM_API_KEY
    )
    if not api_key:
        return None

    payload = {
        "model": settings.RERANK_MODEL,
        "query": query,
        "documents": documents,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{base_url}/rerank", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"⚠️ rerank 调用失败（回退到余弦相似度）: {e}")
        return None

    # 结果形如 {"results": [{"index": 0, "relevance_score": 0.9}, ...]}
    scores = [0.0] * len(documents)
    for item in data.get("results", []):
        idx = item.get("index")
        if idx is not None and 0 <= idx < len(documents):
            scores[idx] = float(item.get("relevance_score", 0.0))
    return scores

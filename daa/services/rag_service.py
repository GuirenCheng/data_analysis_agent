"""RAG 服务 — 嵌入、索引、语义检索。"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from daa.models.session import AnalysisSession


async def search_similar(
    db: AsyncSession,
    user_id: str,
    query: str,
    top_k: int = 5,
    content_type: Optional[str] = None,
) -> list[dict]:
    """语义搜索相似的历史分析内容。

    Args:
        db: 数据库会话
        user_id: 用户 ID
        query: 搜索查询文本
        top_k: 返回结果数量
        content_type: 可选过滤: query | code | report | figure_caption

    Returns:
        相似结果列表
    """
    # 尝试从 ChromaDB 检索
    try:
        from daa.rag.retriever import RAGRetriever
        retriever = RAGRetriever()
        results = await retriever.retrieve_context(
            user_id=user_id,
            current_query=query,
            top_k=top_k,
            content_types=[content_type] if content_type else None,
        )
        return [
            {
                "content_text": r.content_text,
                "content_type": r.content_type,
                "source_session_id": r.source_session_id,
                "similarity": r.similarity,
            }
            for r in results
        ]
    except Exception:
        pass

    # 回退：空结果
    return []


async def index_session(
    db: AsyncSession, session_id: str, user_id: str
) -> int:
    """索引一个已完成分析会话的内容到 ChromaDB。

    Args:
        db: 数据库会话
        session_id: 会话 ID
        user_id: 用户 ID

    Returns:
        索引的文档块数量
    """
    from daa.models.analysis_step import AnalysisStep

    # 获取会话的所有步骤
    result = await db.execute(
        select(AnalysisStep)
        .where(AnalysisStep.session_id == session_id)
        .order_by(AnalysisStep.round_number)
    )
    steps = list(result.scalars().all())

    if not steps:
        return 0

    try:
        from daa.rag.indexer import RAGIndexer
        indexer = RAGIndexer()
        count = await indexer.index_steps(
            user_id=user_id,
            session_id=session_id,
            steps=steps,
        )
        return count
    except Exception:
        return 0

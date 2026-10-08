"""RAG API — 语义搜索历史分析。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from daa.db.session import get_db
from daa.middleware.auth import get_current_user
from daa.models.user import User
from daa.schemas.rag import RagSearchResponse, RagSearchResult
from daa.services.rag_service import search_similar

router = APIRouter(prefix="/rag")


@router.get("/search", response_model=RagSearchResponse)
async def search_rag(
    q: str = Query(..., min_length=1, description="搜索查询"),
    top_k: int = Query(default=5, ge=1, le=20),
    content_type: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """语义搜索历史分析内容。

    支持的 content_type: query, code, report, figure_caption
    """
    results = await search_similar(
        db, user.id, q, top_k=top_k, content_type=content_type
    )

    return RagSearchResponse(
        results=[RagSearchResult(**r) for r in results],
        query=q,
        total_found=len(results),
    )

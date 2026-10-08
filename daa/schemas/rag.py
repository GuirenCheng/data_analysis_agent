"""RAG 搜索 schemas。"""

from pydantic import BaseModel, Field


class RagSearchResult(BaseModel):
    """RAG 搜索结果项。"""

    content_text: str
    content_type: str = ""
    source_session_id: str = ""
    similarity: float = 0.0
    metadata: dict = Field(default_factory=dict)


class RagSearchResponse(BaseModel):
    """RAG 搜索响应。"""

    results: list[RagSearchResult] = Field(default_factory=list)
    query: str = ""
    total_found: int = 0

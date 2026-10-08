"""RAG 索引器 — 将分析内容索引到 ChromaDB。"""

import uuid
from typing import Optional

from daa.rag.embedder import Embedder
from daa.rag.splitter import TextSplitter


class RAGIndexer:
    """RAG 索引管道。

    将分析会话的内容（查询、代码、报告、图表描述）分块嵌入后存入 ChromaDB。
    """

    def __init__(self, chroma_client=None):
        self.splitter = TextSplitter()

        # Lazy import to avoid dependency issues when ChromaDB is not available
        self._chroma_client = chroma_client
        self._embedder: Optional[Embedder] = None

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
            except Exception as e:
                print(f"⚠️ ChromaDB 初始化失败: {e}")
                return None
        return self._chroma_client

    async def _get_or_create_collection(self, collection_name: str):
        """获取或创建 ChromaDB 集合。"""
        client = await self._get_chroma()
        if client is None:
            return None
        try:
            return client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception:
            return None

    async def index_steps(
        self,
        user_id: str,
        session_id: str,
        steps: list,
    ) -> int:
        """索引一个分析会话的所有步骤。

        Args:
            user_id: 用户 ID
            session_id: 会话 ID
            steps: AnalysisStep ORM 实例列表

        Returns:
            索引的文档块总数
        """
        embedder = self._get_embedder()
        total_count = 0

        for step in steps:
            # 索引查询（每个会话的第一轮）
            if step.round_number == 1 and step.response_text:
                count = await self._index_text(
                    collection_name="analysis_queries",
                    user_id=user_id,
                    session_id=session_id,
                    content_type="query",
                    text=step.response_text[:2000],  # 截断过长的响应
                    embedder=embedder,
                )
                total_count += count

            # 索引成功的代码
            if step.action == "generate_code" and step.execution_success and step.code:
                chunks = self.splitter.split_code(step.code)
                for chunk in chunks:
                    count = await self._index_text(
                        collection_name="analysis_code",
                        user_id=user_id,
                        session_id=session_id,
                        content_type="code",
                        text=chunk,
                        embedder=embedder,
                    )
                    total_count += count

            # 索引图表分析
            if step.action == "collect_figures" and step.figures_collected:
                figures = step.figures_collected if isinstance(step.figures_collected, list) else []
                for fig in figures:
                    if isinstance(fig, dict):
                        desc = fig.get("analysis", "") or fig.get("description", "")
                        if desc:
                            count = await self._index_text(
                                collection_name="analysis_figures",
                                user_id=user_id,
                                session_id=session_id,
                                content_type="figure_caption",
                                text=desc,
                                embedder=embedder,
                            )
                            total_count += count

        return total_count

    async def index_report(
        self,
        user_id: str,
        session_id: str,
        report_content: str,
    ) -> int:
        """索引最终报告。"""
        embedder = self._get_embedder()
        chunks = self.splitter.split_report(report_content)
        count = 0
        for chunk in chunks:
            c = await self._index_text(
                collection_name="analysis_reports",
                user_id=user_id,
                session_id=session_id,
                content_type="report",
                text=chunk,
                embedder=embedder,
            )
            count += c
        return count

    async def _index_text(
        self,
        collection_name: str,
        user_id: str,
        session_id: str,
        content_type: str,
        text: str,
        embedder: Embedder,
    ) -> int:
        """将单段文本嵌入后索引到 ChromaDB。"""
        if not text.strip():
            return 0

        collection = await self._get_or_create_collection(collection_name)
        if collection is None:
            return 0

        try:
            embedding = embedder.embed_text(text)
            chroma_id = str(uuid.uuid4())

            collection.add(
                ids=[chroma_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    "user_id": user_id,
                    "source_session_id": session_id,
                    "content_type": content_type,
                }],
            )
            return 1
        except Exception as e:
            print(f"⚠️ 索引文本失败: {e}")
            return 0

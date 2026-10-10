"""重建 RAG 索引。

清空 ChromaDB 中所有集合，并从 MySQL 中重新向量化所有「已完成」的分析会话
（用户查询 / 成功代码 / 图表描述 / 最终报告），再写回向量库。

适用场景：
  - 更换 embedding 模型（向量维度变化导致旧索引不可用）
  - ChromaDB 数据损坏 / 需要全量重建

用法：
    python scripts/rebuild_index.py
"""

import asyncio
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，以便独立运行 `python scripts/rebuild_index.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from daa.db.session import get_engine, get_session_factory
from daa.models.analysis_step import AnalysisStep
from daa.models.session import AnalysisSession
from daa.rag.indexer import RAGIndexer
from daa.services.rag_service import index_session

# 与 indexer/retriever 使用的集合名保持一致
COLLECTIONS = [
    "analysis_queries",
    "analysis_code",
    "analysis_figures",
    "analysis_reports",
]


async def clear_collections() -> None:
    """删除旧的 ChromaDB 集合，保证以全新维度重建。"""
    import chromadb

    from daa.settings import get_settings

    client = chromadb.PersistentClient(path=get_settings().CHROMA_PERSIST_DIR)
    for name in COLLECTIONS:
        try:
            client.delete_collection(name)
            print(f"  已删除集合 {name}")
        except Exception:
            # 集合不存在时忽略
            pass


async def rebuild() -> int:
    await clear_collections()

    factory = await get_session_factory()
    async with factory() as db:
        result = await db.execute(
            select(AnalysisSession).where(AnalysisSession.status == "completed")
        )
        sessions = list(result.scalars().all())

    print(f"共 {len(sessions)} 个已完成会话，开始重建索引…\n")

    total = 0
    indexer = RAGIndexer()

    for session in sessions:
        async with factory() as db:
            # 1) 用户查询 / 成功代码 / 图表描述
            n_steps = await index_session(
                db, session_id=session.id, user_id=session.user_id
            )

            # 2) 最终报告（取 round_number 最大的 analysis_complete 步骤）
            report_result = await db.execute(
                select(AnalysisStep)
                .where(
                    AnalysisStep.session_id == session.id,
                    AnalysisStep.action == "analysis_complete",
                )
                .order_by(AnalysisStep.round_number.desc())
            )
            report_step = report_result.scalars().first()
            n_report = 0
            if report_step and report_step.response_text:
                n_report = await indexer.index_report(
                    user_id=session.user_id,
                    session_id=session.id,
                    report_content=report_step.response_text,
                )

        chunk = n_steps + n_report
        total += chunk
        print(f"  session {session.id[:8]} → {chunk} 块 (步骤 {n_steps} + 报告 {n_report})")

    print(f"\n完成，共索引 {total} 个文档块。")
    return total


async def main() -> None:
    await rebuild()
    engine = await get_engine()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

"""分析服务 — 编排完整的分析生命周期。"""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from daa.core.executor_registry import remove_executor
from daa.db.redis import cache, get_redis
from daa.models.analysis_step import AnalysisStep
from daa.models.session import AnalysisSession
from daa.settings import get_settings
from daa.workflow.graph import get_analysis_graph
from daa.workflow.state import AnalysisState


async def run_analysis(
    session_id: str,
    user_query: str,
    file_paths: list[str],
    max_rounds: int,
    output_dir: str,
    user_id: str,
) -> dict:
    """执行完整的分析工作流（LangGraph 状态机）。

    此函数由 ARQ worker 在后台调用。

    Args:
        session_id: 分析会话 ID（用于 Redis 进度更新）
        user_query: 用户自然语言需求
        file_paths: 数据文件路径列表
        max_rounds: 最大分析轮次
        output_dir: 输出根目录
        user_id: 用户 ID（用于 RAG 检索按用户过滤）

    Returns:
        最终状态字典
    """
    graph = get_analysis_graph()

    # 检索相关历史分析作为 RAG 上下文（失败时静默跳过，不影响主流程）
    rag_context = ""
    try:
        from daa.rag.retriever import RAGRetriever, format_rag_context_for_prompt

        retriever = RAGRetriever()
        contexts = await retriever.retrieve_context(
            user_id=user_id,
            current_query=user_query,
            top_k=get_settings().RAG_TOP_K,
        )
        rag_context = format_rag_context_for_prompt(contexts)
    except Exception as e:
        print(f"⚠️ RAG 检索失败（将跳过历史参考）: {e}")

    initial_state: AnalysisState = {
        "user_query": user_query,
        "file_paths": file_paths,
        "max_rounds": max_rounds,
        "session_output_dir": output_dir,
        "messages": [],
        "current_round": 0,
        "analysis_results": [],
        "collected_figures": [],
        "rag_context": rag_context,
        "action": "",
        "error_count": 0,
        "final_report": "",
    }

    # 配置 LangGraph checkpoint（使用 session_id 作为 thread_id 支持恢复）
    config = {"configurable": {"thread_id": session_id}}

    # 更新 Redis 状态 → running（用原始 redis 客户端，避免字符串被 JSON 双重编码）
    redis = await get_redis()
    await redis.set(f"session:{session_id}:status", "running")
    await redis.set(f"session:{session_id}:progress", 0.0)

    try:
        # 流式执行工作流。stream_mode="values" 返回每一步的完整累积状态，
        # 这样 final_state 才能拿到 current_round / analysis_results 等字段
        # （默认 "updates" 只返回节点部分更新，会丢失这些值）。
        final_state = None
        async for state in graph.astream(initial_state, config, stream_mode="values"):
            current_round = state.get("current_round", 0)
            max_r = state.get("max_rounds", max_rounds)
            if max_r > 0:
                progress = min(current_round / max_r, 0.95)
                await redis.set(f"session:{session_id}:progress", progress)
                await redis.set(f"session:{session_id}:current_round", current_round)

            final_state = state

        # 标记完成
        await redis.set(f"session:{session_id}:status", "completed")
        await redis.set(f"session:{session_id}:progress", 1.0)

        return final_state or {}

    except Exception as e:
        # 标记失败
        await redis.set(f"session:{session_id}:status", "failed")
        await redis.set(f"session:{session_id}:error", str(e))
        raise


async def persist_step(
    db: AsyncSession, session_id: str, round_number: int, action: str, **kwargs
) -> AnalysisStep:
    """持久化分析步骤到 MySQL。"""
    step = AnalysisStep(
        id=str(uuid.uuid4()),
        session_id=session_id,
        round_number=round_number,
        action=action,
        code=kwargs.get("code"),
        response_text=kwargs.get("response_text"),
        execution_output=kwargs.get("execution_output"),
        execution_error=kwargs.get("execution_error"),
        execution_success=kwargs.get("execution_success"),
        figures_collected=kwargs.get("figures_collected"),
    )
    db.add(step)
    await db.flush()
    return step


async def cancel_analysis(
    db: AsyncSession, session_id: str, user_id: str
) -> bool:
    """取消正在运行的分析。"""
    from daa.models.session import AnalysisSession
    from sqlalchemy import select

    result = await db.execute(
        select(AnalysisSession).where(
            AnalysisSession.id == session_id,
            AnalysisSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        return False
    if session.status not in ("pending", "running"):
        return False

    session.status = "cancelled"
    session.completed_at = datetime.now()
    await db.flush()

    # 清理 Redis
    await cache.delete(f"session:{session_id}:status")
    await cache.delete(f"session:{session_id}:progress")

    # 清理执行器
    if session.output_dir:
        remove_executor(session.output_dir)

    return True

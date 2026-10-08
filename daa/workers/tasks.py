"""ARQ 异步任务定义。"""

from datetime import datetime

from daa.core.executor_registry import remove_executor, reset_all
from daa.db.redis import cache, get_redis
from daa.services.analysis_service import run_analysis
from daa.settings import get_settings


async def run_analysis_task(
    ctx: dict,
    session_id: str,
    user_query: str,
    file_paths: list[str],
    max_rounds: int,
    user_id: str,
) -> dict:
    """后台运行数据分析任务。

    由 API 层通过 ARQ 入队，在 worker 进程中执行 LangGraph 工作流。
    通过 Redis 将进度推送给 SSE 端点。

    Args:
        ctx: ARQ worker 上下文
        session_id: 分析会话 ID
        user_query: 用户自然语言需求
        file_paths: 数据文件路径列表
        max_rounds: 最大分析轮次
        user_id: 用户 ID

    Returns:
        最终状态字典
    """
    settings = get_settings()
    output_dir = settings.DEFAULT_OUTPUT_DIR

    try:
        # 更新会话状态为 running
        from daa.db.session import get_session_factory

        factory = await get_session_factory()
        async with factory() as db:
            from daa.services.session_service import update_session_status
            await update_session_status(
                db, session_id, status="running", progress=0.0
            )
            await db.commit()

        # 执行分析
        final_state = await run_analysis(
            session_id=session_id,
            user_query=user_query,
            file_paths=file_paths,
            max_rounds=max_rounds,
            output_dir=output_dir,
            user_id=user_id,
        )

        # 更新会话为已完成
        async with factory() as db:
            from daa.services.session_service import update_session_status
            from daa.services.analysis_service import persist_step

            final_report = final_state.get("final_report", "")
            report_path = final_state.get("report_file_path", "")
            session_dir = final_state.get("session_output_dir", "")
            current_round = final_state.get("current_round", 0)

            await update_session_status(
                db,
                session_id,
                status="completed",
                progress=1.0,
                output_dir=session_dir,
                report_path=report_path,
                current_round=current_round,
            )

            # 持久化中间步骤（每一轮的代码执行 / 图表收集）
            for item in final_state.get("analysis_results", []):
                round_number = item.get("round", 0)
                if "collected_figures" in item:
                    await persist_step(
                        db,
                        session_id,
                        round_number=round_number,
                        action="collect_figures",
                        response_text=item.get("response"),
                        figures_collected=item.get("collected_figures"),
                    )
                else:
                    result = item.get("result") or {}
                    await persist_step(
                        db,
                        session_id,
                        round_number=round_number,
                        action="execute_code",
                        code=item.get("code"),
                        response_text=item.get("response"),
                        execution_output=result.get("output"),
                        execution_error=result.get("error"),
                        execution_success=result.get("success"),
                    )

            # 持久化最终步骤
            await persist_step(
                db,
                session_id,
                round_number=current_round,
                action="analysis_complete",
                response_text=final_report,
            )
            await db.commit()

        # RAG 索引
        try:
            from daa.rag.indexer import RAGIndexer
            indexer = RAGIndexer()
            await indexer.index_report(
                user_id=user_id,
                session_id=session_id,
                report_content=final_report,
            )
        except Exception as e:
            print(f"⚠️ RAG 索引失败: {e}")

        return {"status": "completed", "session_id": session_id}

    except Exception as e:
        # 更新为失败状态
        try:
            factory = await get_session_factory()
            async with factory() as db:
                from daa.services.session_service import update_session_status
                await update_session_status(
                    db,
                    session_id,
                    status="failed",
                    error_message=str(e),
                )
                await db.commit()
        except Exception:
            pass

        # 清理执行器
        remove_executor(f"{output_dir}/session_*")

        raise

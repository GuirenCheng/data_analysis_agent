"""分析 API — 分析步骤查询、报告获取、进度流、取消。"""

import asyncio
import json
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from daa.db.redis import get_redis
from daa.db.session import get_db
from daa.middleware.auth import get_current_user
from daa.models.user import User
from daa.schemas.analysis import AnalysisStepOut, ReportOut
from daa.schemas.common import ErrorResponse, StatusResponse
from daa.services.analysis_service import cancel_analysis
from daa.services.report_service import get_report

router = APIRouter(prefix="/analyses")


@router.get("/{session_id}/steps")
async def list_analysis_steps(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分析会话的所有步骤。"""
    from daa.models.analysis_step import AnalysisStep
    from sqlalchemy import select

    result = await db.execute(
        select(AnalysisStep)
        .where(AnalysisStep.session_id == session_id)
        .order_by(AnalysisStep.round_number)
    )
    steps = result.scalars().all()

    # 验证所有权
    from daa.services.session_service import get_session
    session = await get_session(db, session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return [AnalysisStepOut.model_validate(s) for s in steps]


@router.get("/{session_id}/report", response_model=ReportOut)
async def get_analysis_report(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分析会话的最终报告。"""
    report = await get_report(db, session_id, user.id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在或分析未完成")

    return ReportOut(
        markdown=report["markdown"],
        figures=report.get("figures", []),
        report_file_path=report.get("report_file_path"),
    )


@router.get("/{session_id}/figures/{filename}")
async def get_session_figure(
    session_id: str,
    filename: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取会话生成的图表图片文件（报告和详情页内嵌图片均通过此端点加载）。

    图片以 `<img src="/api/v1/analyses/{session_id}/figures/{filename}?token=...">`
    的方式访问，`?token=` 用于绕过浏览器 `<img>` 无法设置 Authorization 头的问题。
    """
    from daa.services.session_service import get_session

    session = await get_session(db, session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 图片目录：优先用 output_dir；旧会话可能未持久化 output_dir，则从 report_path 反推
    base_dir = session.output_dir
    if not base_dir and session.report_path:
        base_dir = str(Path(session.report_path).parent)
    if not base_dir:
        raise HTTPException(status_code=404, detail="会话输出目录不存在")

    # 仅取文件名（basename），防止路径穿越
    safe_name = os.path.basename(filename)
    file_path = os.path.join(base_dir, safe_name)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="图片不存在")

    return FileResponse(file_path)


@router.get("/{session_id}/stream")
async def stream_progress(
    session_id: str,
    user: User = Depends(get_current_user),
):
    """SSE 端点 — 实时推送分析进度。"""
    # 验证所有权
    from daa.db.redis import get_redis as _get_redis
    redis = await _get_redis()

    async def event_generator():
        last_progress = -1.0
        while True:
            status = (await redis.get(f"session:{session_id}:status")) or "pending"
            progress = float(
                (await redis.get(f"session:{session_id}:progress")) or 0.0
            )

            if isinstance(status, bytes):
                status = status.decode() if isinstance(status, bytes) else status

            if abs(progress - last_progress) > 0.01:
                event_data = json.dumps({
                    "status": status,
                    "progress": progress,
                    "current_round": int(
                        (await redis.get(f"session:{session_id}:current_round")) or 0
                    ),
                })
                yield f"data: {event_data}\n\n"
                last_progress = progress

            if status in ("completed", "failed", "cancelled"):
                event_data = json.dumps({"status": status, "progress": progress})
                yield f"data: {event_data}\n\n"
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/cancel", response_model=StatusResponse)
async def cancel_analysis_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消正在运行的分析任务。"""
    success = await cancel_analysis(db, session_id, user.id)
    if not success:
        raise HTTPException(
            status_code=400, detail="会话不存在或状态不允许取消"
        )
    await db.commit()
    return StatusResponse(status="cancelled", message="分析任务已取消")

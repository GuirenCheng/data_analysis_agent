"""会话 API — 分析会话的 CRUD。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from daa.db.session import get_db
from daa.middleware.auth import get_current_user
from daa.models.user import User
from daa.schemas.common import DeletedResponse, PaginationParams
from daa.schemas.session import (
    SessionCreate,
    SessionDetailOut,
    SessionListOut,
    SessionOut,
)
from daa.services.session_service import (
    create_session,
    delete_session,
    get_session,
    list_sessions,
)

router = APIRouter(prefix="/sessions")


@router.get("", response_model=SessionListOut)
async def list_user_sessions(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None, description="按状态筛选"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出当前用户的所有分析会话。"""
    sessions, total = await list_sessions(
        db, user.id, page=page, per_page=per_page, status=status
    )
    return SessionListOut(
        items=[SessionOut.model_validate(s) for s in sessions],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_analysis_session(
    request: SessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新的分析会话（自动触发后台分析任务）。"""
    session = await create_session(
        db,
        user_id=user.id,
        query=request.query,
        max_rounds=request.max_rounds,
        file_ids=request.file_ids,
    )
    await db.commit()

    return SessionOut.model_validate(session)


@router.get("/{session_id}", response_model=SessionDetailOut)
async def get_session_detail(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个会话详情（含步骤和图表）。"""
    session = await get_session(db, session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 加载关联数据（显式查询，lazy="dynamic" 关系不支持 async for）
    from sqlalchemy import select

    from daa.models.analysis_step import AnalysisStep

    result = await db.execute(
        select(AnalysisStep)
        .where(AnalysisStep.session_id == session_id)
        .order_by(AnalysisStep.round_number)
    )
    steps_list = list(result.scalars().all())
    figures_list = []
    for step in steps_list:
        if step.action == "collect_figures" and step.figures_collected:
            if isinstance(step.figures_collected, list):
                figures_list.extend(step.figures_collected)

    from daa.schemas.analysis import AnalysisStepOut, FigureOut

    detail = SessionDetailOut(
        **SessionOut.model_validate(session).model_dump(),
        steps=[AnalysisStepOut.model_validate(s) for s in steps_list],
        figures=[FigureOut(**f) if isinstance(f, dict) else f for f in figures_list],
    )
    return detail


@router.delete("/{session_id}", response_model=DeletedResponse)
async def remove_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除分析会话。"""
    deleted = await delete_session(db, session_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    await db.commit()
    return DeletedResponse(id=session_id)

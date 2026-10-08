"""会话服务 — 分析会话的 CRUD 操作。"""

import logging
import uuid
from typing import Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from daa.models.session import AnalysisSession

logger = logging.getLogger(__name__)


async def create_session(
    db: AsyncSession,
    user_id: str,
    query: str,
    max_rounds: int = 20,
    file_ids: Optional[list[str]] = None,
) -> AnalysisSession:
    """创建新的分析会话并触发后台分析任务。

    1. 创建 AnalysisSession 数据库记录（状态: pending）
    2. 将 file_ids 解析为实际文件路径
    3. 将分析任务入队到 ARQ worker
    4. 关联上传文件到本次会话
    """
    session = AnalysisSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        query=query,
        max_rounds=max_rounds,
        status="pending",
    )
    db.add(session)
    await db.flush()

    # ── 解析文件 ID → 实际路径 ──────────
    file_paths: list[str] = []
    if file_ids:
        from daa.services.file_service import get_file as get_uploaded_file
        for fid in file_ids:
            f = await get_uploaded_file(db, fid, user_id)
            if f is not None:
                file_paths.append(f.stored_path)
                f.session_id = session.id  # 关联文件到本次会话

    # ── 入队 ARQ 后台分析任务 ────────────
    try:
        from daa.db.redis import get_arq_redis
        arq_redis = await get_arq_redis()
        await arq_redis.enqueue_job(
            "run_analysis_task",
            session.id,
            query,
            file_paths,
            max_rounds,
            user_id,
        )
        logger.info(f"分析任务已入队: session={session.id}")
    except Exception as exc:
        # ARQ / Redis 不可用时记录警告，会话保持 pending 状态
        logger.warning(
            f"无法入队分析任务 (session={session.id}): {exc}，"
            f"会话将保持 pending 状态"
        )

    return session


async def get_session(
    db: AsyncSession, session_id: str, user_id: Optional[str] = None
) -> Optional[AnalysisSession]:
    """获取单个会话详情。"""
    stmt = select(AnalysisSession).where(AnalysisSession.id == session_id)
    if user_id:
        stmt = stmt.where(AnalysisSession.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
) -> tuple[list[AnalysisSession], int]:
    """分页列出用户的会话。"""
    # 计数
    count_stmt = select(func.count(AnalysisSession.id)).where(
        AnalysisSession.user_id == user_id
    )
    if status:
        count_stmt = count_stmt.where(AnalysisSession.status == status)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 分页查询
    stmt = (
        select(AnalysisSession)
        .where(AnalysisSession.user_id == user_id)
    )
    if status:
        stmt = stmt.where(AnalysisSession.status == status)
    stmt = stmt.order_by(desc(AnalysisSession.created_at))
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(stmt)
    sessions = list(result.scalars().all())

    return sessions, total


async def update_session_status(
    db: AsyncSession,
    session_id: str,
    status: str,
    progress: Optional[float] = None,
    error_message: Optional[str] = None,
    output_dir: Optional[str] = None,
    report_path: Optional[str] = None,
    current_round: Optional[int] = None,
) -> Optional[AnalysisSession]:
    """更新会话状态。"""
    session = await get_session(db, session_id)
    if not session:
        return None

    session.status = status
    if progress is not None:
        session.progress = progress
    if error_message is not None:
        session.error_message = error_message
    if output_dir is not None:
        session.output_dir = output_dir
    if report_path is not None:
        session.report_path = report_path
    if current_round is not None:
        session.current_round = current_round

    from datetime import datetime
    if status == "running" and not session.started_at:
        session.started_at = datetime.now()
    elif status in ("completed", "failed", "cancelled"):
        session.completed_at = datetime.now()

    await db.flush()
    return session


async def delete_session(
    db: AsyncSession, session_id: str, user_id: str
) -> bool:
    """删除会话（仅允许所有者删除）。"""
    session = await get_session(db, session_id, user_id)
    if not session:
        return False
    await db.delete(session)
    await db.flush()
    return True

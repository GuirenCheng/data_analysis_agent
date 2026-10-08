"""报告服务 — Markdown 报告获取和 Word 文档生成。"""

from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from daa.models.session import AnalysisSession


async def get_report(
    db: AsyncSession, session_id: str, user_id: str
) -> Optional[dict]:
    """获取分析会话的最终报告。

    Returns:
        {"markdown": str, "figures": list[dict], "report_file_path": str} 或 None
    """
    result = await db.execute(
        select(AnalysisSession).where(
            AnalysisSession.id == session_id,
            AnalysisSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session or not session.report_path:
        return None

    # 读取报告文件
    try:
        report_content = Path(session.report_path).read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        report_content = "报告文件不可用"

    # 收集图表信息
    from daa.models.analysis_step import AnalysisStep

    steps_result = await db.execute(
        select(AnalysisStep)
        .where(AnalysisStep.session_id == session_id)
        .order_by(AnalysisStep.round_number)
    )
    steps = list(steps_result.scalars().all())

    figures: list[dict] = []
    for step in steps:
        if step.action == "collect_figures" and step.figures_collected:
            figures.extend(step.figures_collected if isinstance(step.figures_collected, list) else [])

    return {
        "markdown": report_content,
        "figures": figures,
        "report_file_path": session.report_path,
    }

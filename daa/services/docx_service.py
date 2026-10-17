"""Word 服务 — 分析报告的 .docx 按需生成与磁盘缓存。

与 PPT 不同，Word 是报告的忠实转换（Markdown → docx），不调用 LLM，直接
渲染。路径解析 / 缓存逻辑与 ppt_service 保持一致。
"""

import os
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from daa.core.docx_gen import render_docx

# 与会话目录下的「最终分析报告.md」同目录、同名（.docx 后缀）
DOCX_FILENAME = "最终分析报告.docx"


async def generate_docx(
    db: AsyncSession, session_id: str, user_id: str
) -> Optional[str]:
    """按需生成会话的 Word 文档，成功后缓存到会话输出目录并返回文件路径。

    已存在则直接返回缓存路径；任一步骤失败返回 None，由 API 层转为 404。
    """
    from daa.services.report_service import get_report
    from daa.services.session_service import get_session

    try:
        session = await get_session(db, session_id, user_id)
        if not session:
            return None

        report = await get_report(db, session_id, user_id)
        if not report:
            return None

        # 输出目录：优先 output_dir，旧会话未持久化则从 report_path 反推
        base_dir = session.output_dir
        if not base_dir and session.report_path:
            base_dir = str(Path(session.report_path).parent)
        if not base_dir:
            return None

        docx_path = os.path.join(base_dir, DOCX_FILENAME)
        if os.path.isfile(docx_path):
            return docx_path

        return render_docx(report["markdown"], base_dir, docx_path)
    except Exception as e:
        print(f"⚠️ Word 生成失败: {e}")
        return None

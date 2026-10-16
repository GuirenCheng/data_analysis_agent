"""PPT 服务 — 分析报告的幻灯片（.pptx）按需生成与磁盘缓存。"""

import os
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from daa.core.slides import build_slide_outline, render_pptx
from daa.llm.chat_models import create_chat_model

# 与会话目录下的「最终分析报告.md」同目录、同名（.pptx 后缀）
PPT_FILENAME = "最终分析报告.pptx"


async def generate_ppt(
    db: AsyncSession, session_id: str, user_id: str
) -> Optional[str]:
    """按需生成会话的 PPT，成功后缓存到会话输出目录并返回文件路径。

    已存在则直接返回缓存路径，不重复调用 LLM；任一步骤失败返回 None，
    由 API 层转为 404/502。
    """
    from daa.services.config_service import get_user_llm_overrides
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

        ppt_path = os.path.join(base_dir, PPT_FILENAME)
        if os.path.isfile(ppt_path):
            return ppt_path

        # 沿用用户自定义 LLM 配置（未启用则回退全局），稳定低温 + 固定 max_tokens
        llm_config = await get_user_llm_overrides(db, user_id)
        chat_model = create_chat_model(
            temperature=0.3,
            max_tokens=8192,
            llm_config=llm_config,
        )

        outline = await build_slide_outline(chat_model, report["markdown"], report["figures"])
        if not outline:
            return None

        return render_pptx(outline, base_dir, ppt_path, title="数据分析报告")
    except Exception as e:
        print(f"⚠️ PPT 生成失败: {e}")
        return None

"""初始化节点 — 创建会话目录、初始化执行器、构建首轮提示词。"""

import uuid
from pathlib import Path

from langchain_core.messages import HumanMessage

from daa.core.executor import CodeExecutor
from daa.workflow.state import AnalysisState


async def init_node(state: AnalysisState) -> dict:
    """初始化数据分析会话。

    职责:
    1. 创建 UUID 会话输出目录
    2. 初始化 IPython 代码执行器
    3. 设置 session_output_dir 环境变量
    4. 构建首轮用户消息

    Args:
        state: 当前工作流状态
    Returns:
        状态更新字典
    """
    base_output_dir: str = state.get("session_output_dir", "outputs")
    user_query: str = state.get("user_query", "")
    file_paths: list[str] = state.get("file_paths", [])

    # ── 1. 创建会话目录 ─────────────────
    session_id = uuid.uuid4().hex
    session_dir = Path(base_output_dir) / f"session_{session_id}"
    session_dir.mkdir(parents=True, exist_ok=True)
    output_dir_str = str(session_dir.resolve())

    # ── 2. 初始化执行器 ─────────────────
    executor = CodeExecutor(output_dir_str)
    executor.set_variable("session_output_dir", output_dir_str)

    # ── 3. 构建首轮提示词 ──────────────
    initial_prompt = f"用户需求: {user_query}"
    if file_paths:
        initial_prompt += f"\n数据文件: {', '.join(file_paths)}"

    # ── 4. 获取环境信息 ─────────────────
    notebook_vars = executor.get_environment_info()

    print(f"🚀 开始数据分析任务")
    print(f"📝 用户需求: {user_query}")
    print(f"📂 输出目录: {output_dir_str}")

    return {
        "session_output_dir": output_dir_str,
        "current_round": 0,
        "max_rounds": state.get("max_rounds", 20),
        "analysis_results": [],
        "collected_figures": [],
        "error_count": 0,
        "messages": [HumanMessage(content=initial_prompt)],
        "notebook_variables": notebook_vars,
    }

"""LangGraph AnalysisState — 数据分析工作流的完整状态定义。"""

from typing import Annotated, Any, Literal

from langgraph.graph.message import add_messages

# 使用 TypedDict 兼容 LangGraph checkpointing
# 注意: 在 Python 3.12+ 中可以使用 typing.TypedDict
try:
    from typing import NotRequired, Required, TypedDict
except ImportError:
    from typing_extensions import NotRequired, Required, TypedDict  # type: ignore[assignment]


class AnalysisState(TypedDict, total=False):
    """数据分析工作流的完整状态。

    此状态在 LangGraph 节点间传递，并通过 MemorySaver checkpoint
    实现断点续跑。每个节点可以返回部分状态更新。
    """

    # ── 请求上下文 ──────────────────────
    user_query: Required[str]  # 用户的自然语言分析需求
    file_paths: NotRequired[list[str]]  # 上传的数据文件路径列表
    max_rounds: NotRequired[int]  # 最大分析轮次
    session_output_dir: NotRequired[str]  # UUID 会话输出目录路径

    # ── 对话历史 (LangChain 消息格式) ───
    messages: NotRequired[Annotated[list, add_messages]]

    # ── 跟踪状态 ────────────────────────
    current_round: NotRequired[int]  # 当前轮次计数
    analysis_results: NotRequired[list[dict[str, Any]]]  # 历史代码执行记录
    collected_figures: NotRequired[list[dict[str, Any]]]  # 累积的图表元数据
    notebook_variables: NotRequired[str]  # IPython 环境变量信息字符串
    rag_context: NotRequired[str]  # RAG 检索到的上下文字符串

    # ── 控制流 ─────────────────────────
    action: NotRequired[str]  # generate_code | collect_figures | analysis_complete
    error_count: NotRequired[int]  # 连续错误计数
    final_report: NotRequired[str]  # 最终报告 Markdown 内容
    report_file_path: NotRequired[str]  # 最终报告文件路径

    # ── 最后执行结果 ───────────────────
    last_code: NotRequired[str]  # 最近一次执行的代码
    last_execution_success: NotRequired[bool]
    last_execution_output: NotRequired[str]
    last_execution_error: NotRequired[str]
    last_execution_feedback: NotRequired[str]  # 格式化的反馈字符串
    last_llm_response: NotRequired[str]  # 最近一次 LLM 原始响应


# 动作类型字面量
ActionType = Literal["generate_code", "collect_figures", "analysis_complete", "unknown"]

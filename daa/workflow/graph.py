"""LangGraph 状态图 — 组装完整的数据分析工作流。

替代原始 DataAnalysisAgent.analyze() 中的 while 循环，
使用有状态的 DAG 执行模型。
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from daa.workflow.edges import route_by_action, should_continue_analysis, should_retry
from daa.workflow.nodes import (
    collect_node,
    error_node,
    execute_node,
    init_node,
    llm_node,
    report_node,
)
from daa.workflow.state import AnalysisState


def build_analysis_graph() -> StateGraph:
    """构建并编译数据分析 LangGraph 工作流。

    节点拓扑:
    ```
    start → initialize → call_llm → [route_by_action]
                                      ├─ execute_code ──→ [should_continue]
                                      │                    ├─ continue → call_llm
                                      │                    └─ stop → generate_report
                                      ├─ collect_figures → call_llm
                                      ├─ generate_report → end
                                      └─ error_handler → [should_retry]
                                                          ├─ retry → call_llm
                                                          └─ abort → generate_report
    ```

    Returns:
        编译后的 CompiledStateGraph 实例
    """
    workflow = StateGraph(AnalysisState)

    # ── 注册节点 ─────────────────────────
    workflow.add_node("initialize", init_node)
    workflow.add_node("call_llm", llm_node)
    workflow.add_node("execute_code", execute_node)
    workflow.add_node("collect_figures", collect_node)
    workflow.add_node("generate_report", report_node)
    workflow.add_node("error_handler", error_node)

    # ── 入口 ────────────────────────────
    workflow.set_entry_point("initialize")

    # ── 边 ──────────────────────────────
    # 初始化后直接进入 LLM
    workflow.add_edge("initialize", "call_llm")

    # LLM 响应后的条件路由
    workflow.add_conditional_edges(
        "call_llm",
        route_by_action,
        {
            "execute_code": "execute_code",
            "collect_figures": "collect_figures",
            "generate_report": "generate_report",
            "error_handler": "error_handler",
        },
    )

    # 代码执行后：继续或结束
    workflow.add_conditional_edges(
        "execute_code",
        should_continue_analysis,
        {
            "continue": "call_llm",
            "stop": "generate_report",
        },
    )

    # 图表收集后：继续分析
    workflow.add_edge("collect_figures", "call_llm")

    # 报告生成是终点
    workflow.add_edge("generate_report", END)

    # 错误处理：重试或放弃
    workflow.add_conditional_edges(
        "error_handler",
        should_retry,
        {
            "retry": "call_llm",
            "abort": "generate_report",
        },
    )

    # ── 编译 ────────────────────────────
    memory = MemorySaver()
    compiled = workflow.compile(checkpointer=memory)

    return compiled


# 全局单例（懒加载）
_analysis_graph: StateGraph | None = None


def get_analysis_graph() -> StateGraph:
    """获取全局编译后的分析工作流实例。"""
    global _analysis_graph
    if _analysis_graph is None:
        _analysis_graph = build_analysis_graph()
    return _analysis_graph

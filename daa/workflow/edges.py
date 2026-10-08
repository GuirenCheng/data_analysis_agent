"""LangGraph 条件路由函数 — 控制工作流中的节点跳转。"""

from daa.workflow.state import ActionType, AnalysisState


# 最大连续错误次数，超过后将强制生成报告
MAX_CONSECUTIVE_ERRORS = 3


def route_by_action(state: AnalysisState) -> str:
    """根据 LLM 返回的 action 字段路由到对应节点。

    generate_code  → execute_code
    collect_figures → collect_figures
    analysis_complete → generate_report
    其他 → error_handler
    """
    action: str = state.get("action", "unknown")

    routing: dict[str, str] = {
        "generate_code": "execute_code",
        "collect_figures": "collect_figures",
        "analysis_complete": "generate_report",
    }

    return routing.get(action, "error_handler")


def should_continue_analysis(state: AnalysisState) -> str:
    """判断是否继续下一轮分析循环。

    continue → 回到 call_llm
    stop     → 进入 generate_report 终端节点
    """
    # 分析完成
    if state.get("action") == "analysis_complete":
        return "stop"

    # 达到最大轮次
    current_round: int = state.get("current_round", 0)
    max_rounds: int = state.get("max_rounds", 20)
    if current_round >= max_rounds:
        return "stop"

    # 连续错误过多
    if state.get("error_count", 0) >= MAX_CONSECUTIVE_ERRORS:
        return "stop"

    return "continue"


def should_retry(state: AnalysisState) -> str:
    """判断错误后是否重试。

    retry → 回到 call_llm
    abort → 进入 generate_report
    """
    if state.get("error_count", 0) < MAX_CONSECUTIVE_ERRORS:
        # 兜底：即使错误计数未累积，达到最大轮次也终止，防止无限循环
        current_round: int = state.get("current_round", 0)
        max_rounds: int = state.get("max_rounds", 20)
        if current_round >= max_rounds:
            return "abort"
        return "retry"
    return "abort"

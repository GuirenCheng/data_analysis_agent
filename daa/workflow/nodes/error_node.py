"""错误处理节点 — 统一的错误恢复逻辑。"""

from langchain_core.messages import HumanMessage

from daa.workflow.state import AnalysisState


async def error_node(state: AnalysisState) -> dict:
    """处理 LLM 调用或代码执行中的错误。

    职责:
    1. 检查错误类型和严重程度
    2. 构建错误反馈消息追加到对话历史
    3. 更新错误计数

    Args:
        state: 当前工作流状态
    Returns:
        状态更新字典
    """
    error_count: int = state.get("error_count", 0)
    last_error: str = state.get("last_execution_error", "")

    print(f"⚠️ 错误处理节点 (连续错误: {error_count})")
    if last_error:
        print(f"   错误详情: {last_error[:200]}")

    # 构建错误反馈
    error_feedback = (
        f"发生错误: {last_error}\n"
        f"请分析错误原因并生成修正后的代码。"
        if last_error
        else "代码执行出现问题，请重新生成正确的代码。"
    )

    messages: list = state.get("messages", [])

    return {
        "messages": messages
        + [HumanMessage(content=f"代码执行反馈:\n{error_feedback}")],
        "last_execution_feedback": error_feedback,
        # 递增连续错误计数，否则 should_retry 永远命中 error_count < 3，
        # 未知 action 会导致无限循环。
        "error_count": error_count + 1,
    }

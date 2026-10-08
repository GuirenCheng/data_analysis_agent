"""代码执行节点 — 在 IPython 沙箱中安全执行 LLM 生成的代码。"""

from daa.core.executor_registry import get_or_create_executor
from daa.core.protocol import extract_code_from_response
from daa.workflow.state import AnalysisState


def _format_feedback(success: bool, output: str, error: str) -> str:
    """格式化执行结果为人类可读的反馈字符串。"""
    if success:
        parts = ["✅ 代码执行成功"]
        if output:
            parts.append(f"📊 输出结果：\n{output}")
        return "\n".join(parts)
    else:
        parts = ["❌ 代码执行失败"]
        if error:
            parts.append(f"错误信息: {error}")
        if output:
            parts.append(f"部分输出: {output}")
        return "\n".join(parts)


async def execute_node(state: AnalysisState) -> dict:
    """执行 LLM 生成的 Python 代码。

    职责:
    1. 从 LLM 响应中提取代码
    2. 在 IPython 沙箱中安全执行
    3. 格式化执行反馈
    4. 更新状态（含错误计数）

    Args:
        state: 当前工作流状态
    Returns:
        状态更新字典
    """
    session_dir: str = state.get("session_output_dir", "outputs")
    executor = get_or_create_executor(session_dir)

    response_text: str = state.get("last_llm_response", "")
    code = extract_code_from_response(response_text)

    if not code:
        print("⚠️ 未从响应中提取到可执行代码")
        return {
            "last_code": "",
            "last_execution_success": False,
            "last_execution_error": "响应中缺少可执行代码",
            "last_execution_feedback": "❌ 响应中缺少可执行代码，请重新生成。",
            "error_count": state.get("error_count", 0) + 1,
        }

    print(f"🔧 执行代码:\n{code[:200]}...")
    print("-" * 40)

    # 执行
    result = executor.execute_code(code)
    success: bool = result.get("success", False)
    output: str = result.get("output", "")
    error: str = result.get("error", "")

    # 更新环境变量信息
    notebook_vars = executor.get_environment_info()

    # 格式化反馈
    feedback = _format_feedback(success, output, error)
    print(f"📋 执行反馈:\n{feedback}")

    # 错误计数
    error_count: int = state.get("error_count", 0)
    if not success:
        error_count += 1
    else:
        error_count = 0  # 成功时重置

    return {
        "last_code": code,
        "last_execution_success": success,
        "last_execution_output": output,
        "last_execution_error": error,
        "last_execution_feedback": feedback,
        "notebook_variables": notebook_vars,
        "error_count": error_count,
        "analysis_results": state.get("analysis_results", []) + [{
            "round": state.get("current_round", 0),
            "code": code,
            "result": result,
            "response": response_text,
        }],
    }

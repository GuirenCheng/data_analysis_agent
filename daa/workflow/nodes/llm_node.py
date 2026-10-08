"""LLM 调用节点 — 通过 LangChain 调用 LLM 获取结构化 YAML 响应。"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from daa.core.protocol import parse_yaml_response
from daa.llm.chat_models import create_chat_model
from daa.llm.prompts import build_analysis_prompt_template
from daa.workflow.state import AnalysisState


def _format_conversation_context(messages: list) -> str:
    """格式化 LangChain 消息列表为对话上下文字符串。"""
    parts: list[str] = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            parts.append(f"用户: {msg.content}")
        elif isinstance(msg, AIMessage):
            parts.append(f"助手: {msg.content}")
        elif isinstance(msg, SystemMessage):
            parts.append(f"系统: {msg.content}")
        else:
            parts.append(f"{type(msg).__name__}: {msg.content}")
    return "\n\n".join(parts)


async def llm_node(state: AnalysisState) -> dict:
    """调用 LLM 获取下一步动作。

    职责:
    1. 构建 ChatPromptTemplate（含 RAG 上下文）
    2. 调用 LangChain ChatOpenAI
    3. 解析 YAML 响应获取 action
    4. 更新状态

    Args:
        state: 当前工作流状态
    Returns:
        状态更新字典
    """
    chat_model = create_chat_model()
    prompt_template = build_analysis_prompt_template()
    chain = prompt_template | chat_model

    # 准备变量
    notebook_vars: str = state.get("notebook_variables", "环境信息不可用")
    rag_context: str = state.get("rag_context", "")
    messages: list = state.get("messages", [])
    conversation_context = _format_conversation_context(messages)

    # 添加最近的执行反馈（如果有）
    last_feedback: str = state.get("last_execution_feedback", "")
    if last_feedback:
        conversation_context += f"\n\n用户: 代码执行反馈:\n{last_feedback}"

    # 调用 LLM
    response = await chain.ainvoke({
        "notebook_variables": notebook_vars,
        "rag_context": rag_context or "（无相关历史分析参考）",
        "conversation_context": conversation_context,
    })

    response_text: str = str(response.content)
    print(f"\n🔄 第 {state.get('current_round', 0) + 1} 轮分析")
    print(f"🤖 助手响应:\n{response_text[:300]}...")

    # 解析响应
    yaml_data = parse_yaml_response(response_text)
    action: str = yaml_data.get("action", "generate_code")

    print(f"🎯 检测到动作: {action}")

    new_round: int = state.get("current_round", 0) + 1

    return {
        "messages": [AIMessage(content=response_text)],
        "action": action,
        "current_round": new_round,
        "last_llm_response": response_text,
        "notebook_variables": notebook_vars,
    }

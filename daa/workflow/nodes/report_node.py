"""报告生成节点 — 生成并保存最终分析报告。"""

from langchain_core.messages import HumanMessage

from daa.core.protocol import parse_yaml_response
from daa.core.reporter import (
    build_code_results_summary,
    build_figures_summary,
    build_final_report_prompt,
    extract_report_from_response,
    save_report,
)
from daa.llm.chat_models import create_report_chat_model
from daa.workflow.state import AnalysisState


async def report_node(state: AnalysisState) -> dict:
    """生成最终分析报告。

    职责:
    1. 汇总所有图表和代码执行结果
    2. 调用 LLM 生成结构化的 Markdown 报告
    3. 保存报告到会话目录
    4. 返回 final_report 内容

    Args:
        state: 当前工作流状态
    Returns:
        状态更新字典（含 final_report 和 report_file_path）
    """
    session_dir: str = state.get("session_output_dir", "outputs")
    current_round: int = state.get("current_round", 0)
    collected_figures: list[dict] = state.get("collected_figures", [])
    analysis_results: list[dict] = state.get("analysis_results", [])

    print(f"\n📊 开始生成最终分析报告...")
    print(f"📂 输出目录: {session_dir}")
    print(f"🔢 总轮数: {current_round}")
    print(f"📈 收集图片: {len(collected_figures)} 个")

    # 构建摘要
    figures_summary = build_figures_summary(collected_figures)
    code_results_summary = build_code_results_summary(analysis_results)

    # 构建提示词
    report_prompt = build_final_report_prompt(
        current_round=current_round,
        session_output_dir=session_dir,
        figures_summary=figures_summary,
        code_results_summary=code_results_summary,
    )

    # 调用 LLM 生成报告
    chat_model = create_report_chat_model()

    from daa.llm.prompts import build_report_prompt_template

    prompt_template = build_report_prompt_template()
    chain = prompt_template | chat_model

    system_prompt = (
        "你将会接收到一个数据分析任务的最终报告请求，"
        "请根据提供的分析结果和图片信息生成完整的分析报告。"
    )

    response = await chain.ainvoke({
        "current_round": current_round,
        "session_output_dir": session_dir,
        "figures_summary": figures_summary,
        "code_results_summary": code_results_summary,
        "report_request": report_prompt,
    })

    response_text: str = str(response.content)

    # 提取并保存报告
    final_report = extract_report_from_response(response_text)
    report_path = save_report(final_report, session_dir)

    print(f"✅ 最终报告生成完成")
    print(f"📄 报告已保存至: {report_path}")

    return {
        "final_report": final_report,
        "report_file_path": report_path,
        "action": "analysis_complete",
    }

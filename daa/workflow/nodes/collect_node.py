"""图表收集节点 — 解析 LLM 收集的图表元数据。"""

import os

from daa.core.protocol import parse_yaml_response
from daa.workflow.state import AnalysisState


async def collect_node(state: AnalysisState) -> dict:
    """收集 LLM 生成的图表元数据。

    职责:
    1. 解析 YAML 中的 figures_to_collect
    2. 验证文件是否存在
    3. 累积到 collected_figures 列表

    Args:
        state: 当前工作流状态
    Returns:
        状态更新字典
    """
    response_text: str = state.get("last_llm_response", "")
    yaml_data = parse_yaml_response(response_text)

    figures_to_collect: list[dict] = yaml_data.get("figures_to_collect", [])

    print(f"📊 收集图片: {len(figures_to_collect)} 个")

    collected: list[dict] = []
    for fig in figures_to_collect:
        figure_number = fig.get("figure_number")
        filename = fig.get("filename", f"figure_{figure_number}.png")
        file_path = fig.get("file_path", "")
        description = fig.get("description", "")
        analysis = fig.get("analysis", "")

        print(f"📈 图片 {figure_number}: {filename}")

        # 验证文件
        if file_path and os.path.exists(file_path):
            print(f"   ✅ 文件存在: {file_path}")
        elif file_path:
            print(f"   ⚠️ 文件不存在: {file_path}")

        collected.append({
            "figure_number": figure_number,
            "filename": filename,
            "file_path": file_path,
            "description": description,
            "analysis": analysis,
        })

    # 累积到已有列表
    existing: list[dict] = state.get("collected_figures", [])

    # 重置错误计数（collect 不是错误）
    return {
        "collected_figures": existing + collected,
        "error_count": 0,
        "analysis_results": state.get("analysis_results", []) + [{
            "round": state.get("current_round", 0),
            "action": "collect_figures",
            "collected_figures": collected,
            "response": response_text,
        }],
        "last_execution_feedback": f"已收集 {len(collected)} 个图片及其分析",
    }

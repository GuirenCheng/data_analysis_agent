"""报告生成逻辑 — 从原始 DataAnalysisAgent._generate_final_report() 提取。"""

import os
import re
import textwrap
from typing import Any

from daa.core.protocol import extract_yaml_from_response, parse_yaml_response


def build_final_report_prompt(
    current_round: int,
    session_output_dir: str,
    figures_summary: str,
    code_results_summary: str,
) -> str:
    """构建最终报告生成的提示词。

    Args:
        current_round: 分析轮数
        session_output_dir: 会话输出目录
        figures_summary: 图片摘要文本
        code_results_summary: 代码执行结果摘要

    Returns:
        格式化的报告生成提示词
    """
    from daa.core.prompts import FINAL_REPORT_SYSTEM_PROMPT

    prompt = FINAL_REPORT_SYSTEM_PROMPT.format(
        current_round=current_round,
        session_output_dir=session_output_dir,
        figures_summary=figures_summary,
        code_results_summary=code_results_summary,
    )

    prompt += """

📁 **图片路径使用说明**：
报告和图片都在同一目录下，请在报告中使用相对路径引用图片：
- 格式：![图片描述](./图片文件名.png)
- 示例：![营业总收入趋势](./营业总收入趋势.png)
- 这样可以确保报告在不同环境下都能正确显示图片
"""
    return prompt


def _extract_final_report_block(response: str) -> str:
    """从包含 `final_report: |` 的 YAML 文本中手动提取报告块。

    当 YAML 整体解析失败时（如报告正文里出现了未缩进行的行，破坏了块标量），
    直接按 `final_report: |` 后的缩进块提取并 dedent，避免把 YAML 包裹文本
    （`action: "analysis_complete"` 等）当成报告内容输出。
    """
    m = re.search(r"final_report\s*:\s*[|>][+-]?\s*\n(?P<body>.*)", response, re.DOTALL)
    if not m:
        return ""

    lines = m.group("body").splitlines()
    # 去掉末尾可能残留的独立闭合围栏行
    while lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    body = "\n".join(lines)
    return textwrap.dedent(body).strip()


def extract_report_from_response(response: str) -> str:
    """从 LLM 响应中提取最终报告内容。

    Args:
        response: LLM 原始响应

    Returns:
        提取的报告 Markdown 文本
    """
    # 1. 优先用 YAML 解析（读取 final_report 字段）
    yaml_data = parse_yaml_response(response)
    if isinstance(yaml_data, dict) and yaml_data.get("action") == "analysis_complete":
        report = yaml_data.get("final_report")
        if isinstance(report, str) and report.strip():
            return report.strip()

    # 2. YAML 整体解析失败时，手动提取 final_report 块
    report = _extract_final_report_block(response)
    if report:
        return report

    # 3. 最后回退：返回去除围栏后的原文
    return extract_yaml_from_response(response)


def save_report(report_content: str, session_output_dir: str) -> str:
    """保存最终报告到文件。

    Args:
        report_content: 报告 Markdown 内容
        session_output_dir: 会话输出目录

    Returns:
        报告文件路径
    """
    report_file_path = os.path.join(session_output_dir, "最终分析报告.md")
    with open(report_file_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    return report_file_path


def build_figures_summary(all_figures: list[dict[str, Any]]) -> str:
    """构建图片信息摘要。

    使用相对路径格式以便在 Markdown 报告中引用。
    """
    if not all_figures:
        return "\n本次分析未生成图片。\n"

    parts = ["\n生成的图片及分析:\n"]
    for i, figure in enumerate(all_figures, 1):
        filename = figure.get("filename", "未知文件名")
        relative_path = f"./{filename}"
        parts.append(f"{i}. {filename}")
        parts.append(f"   相对路径: {relative_path}")
        parts.append(f"   描述: {figure.get('description', '无描述')}")
        parts.append(f"   分析: {figure.get('analysis', '无分析')}")
        parts.append("")
    return "\n".join(parts)


def build_code_results_summary(analysis_results: list[dict[str, Any]]) -> str:
    """构建成功执行代码块的摘要。"""
    parts: list[str] = []
    success_count = 0

    for result in analysis_results:
        if result.get("action") == "collect_figures":
            continue
        if not result.get("code"):
            continue

        exec_result = result.get("result", {})
        if exec_result.get("success"):
            success_count += 1
            parts.append(f"代码块 {success_count}: 执行成功")
            output = exec_result.get("output", "")
            if output:
                parts.append(f"输出: {output}")
            parts.append("")

    if not parts:
        return "无成功的代码执行记录。"
    return "\n".join(parts)

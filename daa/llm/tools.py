"""LangChain Tool 定义 — 预留，用于未来从 YAML 协议迁移到原生 tool-calling。

当前版本保留 YAML 协议以维持向后兼容，此文件为未来升级提供入口点。
"""

from langchain_core.tools import tool


@tool
def execute_python_code(code: str) -> str:
    """在沙箱中执行 Python 数据分析代码并返回结果。

    Args:
        code: 有效的 Python 代码字符串
    """
    # 此工具在工作流节点中通过 CodeExecutor 实现
    # 此定义仅作为 LangChain tool-calling 的 schema 参考
    return ""


@tool
def collect_generated_figures(figure_numbers: list[int]) -> str:
    """收集当前会话中已生成图表的元数据。

    Args:
        figure_numbers: 要收集的图表编号列表
    """
    return ""


@tool
def finalize_analysis(report: str) -> str:
    """标记分析完成并提交最终报告。

    Args:
        report: Markdown 格式的完整分析报告
    """
    return ""

"""核心模块 — 保留并增强的原始分析逻辑。

包含:
- prompts: 系统提示词（定义 agent 行为协议）
- protocol: 统一 YAML 解析和代码提取
- safety: 增强 AST 安全检查
- executor: IPython 沙箱代码执行器
- reporter: 报告生成逻辑
"""

from daa.core.protocol import (
    extract_code_from_response,
    extract_yaml_from_response,
    parse_yaml_response,
)
from daa.core.safety import ALLOWED_IMPORTS, check_code_safety
from daa.core.prompts import DATA_ANALYSIS_SYSTEM_PROMPT, FINAL_REPORT_SYSTEM_PROMPT

# CodeExecutor 需要 IPython — 延迟导入以避免非 IPython 环境的导入错误


def _get_code_executor():
    from daa.core.executor import CodeExecutor
    return CodeExecutor


__all__ = [
    "CodeExecutor",
    "check_code_safety",
    "ALLOWED_IMPORTS",
    "parse_yaml_response",
    "extract_yaml_from_response",
    "extract_code_from_response",
    "DATA_ANALYSIS_SYSTEM_PROMPT",
    "FINAL_REPORT_SYSTEM_PROMPT",
]


def __getattr__(name):
    if name == "CodeExecutor":
        return _get_code_executor()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

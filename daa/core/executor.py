"""安全的代码执行器 — 基于 IPython 提供持久化的代码执行沙箱。

从 utils/code_executor.py 重构，集成增强的 AST 安全检查器。
"""

import os
import traceback
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import Any

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

from daa.core.safety import check_code_safety


class CodeExecutor:
    """安全的代码执行器 — 限制依赖库，捕获输出，支持图片保存。"""

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir: str = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

        # IPython 单例 shell
        self.shell: InteractiveShell = InteractiveShell.instance()

        self._setup_chinese_font()
        self._setup_common_imports()
        self.image_counter: int = 0

    # ── 初始化 ────────────────────────────────

    def _setup_chinese_font(self) -> None:
        """设置 matplotlib 中文字体。"""
        try:
            matplotlib.use("Agg")
            plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans", "Arial Unicode MS"]
            plt.rcParams["axes.unicode_minus"] = False

            self.shell.run_cell("""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
""")
        except Exception as e:
            print(f"设置中文字体失败: {e}")

    def _setup_common_imports(self) -> None:
        """预导入常用数据分析库。"""
        common_imports = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import duckdb
import os
import json
from IPython.display import display
"""
        try:
            self.shell.run_cell(common_imports)
            from IPython.display import display

            self.shell.user_ns["display"] = display
        except Exception as e:
            print(f"预导入库失败: {e}")

    # ── 表格输出格式化 ────────────────────────

    def _format_table_output(self, obj: Any) -> str:
        """格式化表格输出，超过 15 行时截断显示。"""
        if hasattr(obj, "shape") and hasattr(obj, "head"):
            rows, cols = obj.shape
            header = f"\n数据表形状: {rows}行 x {cols}列\n列名: {list(obj.columns)}\n"
            if rows <= 15:
                return header + str(obj)
            else:
                head_part = str(obj.head(5))
                tail_part = str(obj.tail(5))
                skipped = rows - 10
                return f"{header}{head_part}\n...\n(省略 {skipped} 行)\n...\n{tail_part}"

        return str(obj)

    # ── 代码执行 ──────────────────────────────

    def execute_code(self, code: str) -> dict[str, Any]:
        """安全地执行 Python 代码并返回结果。

        Args:
            code: 待执行的 Python 代码字符串

        Returns:
            {"success": bool, "output": str, "error": str, "variables": dict}
        """
        # 安全检查
        is_safe, safety_error = check_code_safety(code)
        if not is_safe:
            return {
                "success": False,
                "output": "",
                "error": f"代码安全检查失败: {safety_error}",
                "variables": {},
            }

        vars_before = set(self.shell.user_ns.keys())
        captured = None

        try:
            with capture_output() as captured:
                result = self.shell.run_cell(code)

            if result.error_before_exec:
                return {
                    "success": False,
                    "output": captured.stdout or "",
                    "error": f"执行前错误: {result.error_before_exec}",
                    "variables": {},
                }

            if result.error_in_exec:
                return {
                    "success": False,
                    "output": captured.stdout or "",
                    "error": f"执行错误: {result.error_in_exec}",
                    "variables": {},
                }

            output = captured.stdout or ""

            # 处理返回值
            if result.result is not None:
                formatted = self._format_table_output(result.result)
                output += f"\n{formatted}"

            # 检测新变量
            vars_after = set(self.shell.user_ns.keys())
            new_vars = vars_after - vars_before

            important_new_vars: dict[str, str] = {}
            for var_name in new_vars:
                if var_name.startswith("_"):
                    continue
                try:
                    var_value = self.shell.user_ns[var_name]
                    if hasattr(var_value, "shape"):
                        important_new_vars[var_name] = (
                            f"{type(var_value).__name__} with shape {var_value.shape}"
                        )
                    elif var_name == "session_output_dir":
                        important_new_vars[var_name] = str(var_value)
                except Exception:
                    pass

            return {
                "success": True,
                "output": output,
                "error": "",
                "variables": important_new_vars,
            }

        except Exception as e:
            captured_output_text = captured.stdout if captured else ""
            return {
                "success": False,
                "output": captured_output_text,
                "error": f"执行异常: {e}\n{traceback.format_exc()}",
                "variables": {},
            }

    # ── 环境管理 ──────────────────────────────

    def reset_environment(self) -> None:
        """重置 IPython 执行环境。"""
        self.shell.reset()
        self._setup_common_imports()
        self._setup_chinese_font()
        plt.close("all")
        self.image_counter = 0

    def set_variable(self, name: str, value: Any) -> None:
        """在 IPython 命名空间中设置变量。"""
        self.shell.user_ns[name] = value

    def get_environment_info(self) -> str:
        """获取当前环境中的重要变量信息，用于系统提示词。

        Returns:
            人类可读的环境信息字符串
        """
        info_parts: list[str] = []
        important_vars: dict[str, str] = {}

        skip_vars = {"In", "Out", "get_ipython", "exit", "quit"}

        for var_name, var_value in self.shell.user_ns.items():
            if var_name.startswith("_") or var_name in skip_vars:
                continue
            try:
                if hasattr(var_value, "shape"):
                    important_vars[var_name] = (
                        f"{type(var_value).__name__} with shape {var_value.shape}"
                    )
                elif var_name == "session_output_dir":
                    important_vars[var_name] = str(var_value)
                elif isinstance(var_value, (int, float, str, bool)) and len(str(var_value)) < 100:
                    important_vars[var_name] = f"{type(var_value).__name__}: {var_value}"
                elif hasattr(var_value, "__module__") and var_value.__module__ in (
                    "pandas",
                    "numpy",
                    "matplotlib.pyplot",
                ):
                    important_vars[var_name] = f"导入的模块: {var_value.__module__}"
            except Exception:
                continue

        if important_vars:
            info_parts.append("当前环境变量:")
            for name, info in important_vars.items():
                info_parts.append(f"- {name}: {info}")
        else:
            info_parts.append("当前环境已预装pandas, numpy, matplotlib等库")

        if "session_output_dir" in self.shell.user_ns:
            info_parts.append(
                f"图片保存目录: session_output_dir = "
                f"'{self.shell.user_ns['session_output_dir']}'"
            )

        return "\n".join(info_parts)

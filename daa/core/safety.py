"""增强的 AST 安全检查器 — 修复原始版本的安全漏洞。

改进点:
- 阻止 os.system, os.popen, subprocess 等属性访问调用
- 检查 importlib 等动态导入
- 阻止 __import__ 和 compile
- 更完整的危险函数列表
"""

import ast
from typing import Tuple

# 允许导入的模块白名单
ALLOWED_IMPORTS: set[str] = {
    # 数据分析核心
    "pandas",
    "pd",
    "numpy",
    "np",
    "matplotlib",
    "matplotlib.pyplot",
    "plt",
    "duckdb",
    "scipy",
    "sklearn",
    # 可视化
    "plotly",
    "dash",
    # 网络
    "requests",
    "urllib",
    # 标准库 — 安全
    "os",
    "os.path",
    "sys",
    "json",
    "csv",
    "datetime",
    "time",
    "math",
    "statistics",
    "re",
    "pathlib",
    "io",
    "collections",
    "itertools",
    "functools",
    "operator",
    "warnings",
    "logging",
    "copy",
    "pickle",
    "gzip",
    "zipfile",
    "typing",
    "dataclasses",
    "enum",
    "sqlite3",
}

# 绝对禁止调用的裸函数名
FORBIDDEN_FUNCTIONS: set[str] = {
    "exec",
    "eval",
    "compile",
    "open",
    "__import__",
    "getattr",
    "setattr",
    "delattr",
    "globals",
    "locals",
    "breakpoint",
}

# 禁止的属性访问调用 (module, function)
FORBIDDEN_ATTRIBUTE_CALLS: set[tuple[str, str]] = {
    ("os", "system"),
    ("os", "popen"),
    ("os", "execv"),
    ("os", "execl"),
    ("os", "execve"),
    ("os", "spawnl"),
    ("os", "spawnv"),
    ("subprocess", "call"),
    ("subprocess", "run"),
    ("subprocess", "Popen"),
    ("subprocess", "check_call"),
    ("subprocess", "check_output"),
    ("sys", "exit"),
}

# 禁止导入的模块
FORBIDDEN_IMPORTS: set[str] = {
    "subprocess",
    "importlib",
    "ctypes",
    "socket",
    "shutil",
    "multiprocessing",
    "threading",
    "signal",
    "code",
    "codeop",
    "compileall",
    "py_compile",
}


def check_code_safety(code: str) -> Tuple[bool, str]:
    """检查代码安全性。

    检查规则:
    1. 不允许导入禁止的模块
    2. 只允许导入白名单中的模块
    3. 不允许调用禁止的裸函数 (exec, eval, open 等)
    4. 不允许调用禁止的属性访问 (os.system, subprocess.call 等)

    Returns:
        (is_safe, error_message) — is_safe 为 True 表示代码安全
    """
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        return False, f"语法错误: {e}"

    for node in ast.walk(tree):
        # ── Import 检查 ──────────────────────
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_IMPORTS:
                    return False, f"禁止导入的模块: {alias.name}"
                if alias.name not in ALLOWED_IMPORTS:
                    return False, f"不在白名单中的导入: {alias.name}"

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in FORBIDDEN_IMPORTS:
                return False, f"禁止导入的模块: {module}"
            # 允许从已知安全模块导入子模块
            if module not in ALLOWED_IMPORTS:
                # 检查是否是安全模块的子模块
                base = module.split(".")[0]
                if base in FORBIDDEN_IMPORTS:
                    return False, f"禁止导入的模块: {module}"
                if base not in ALLOWED_IMPORTS:
                    return False, f"不在白名单中的导入: {module}"

        # ── 危险函数调用检查 ──────────────────
        elif isinstance(node, ast.Call):
            # 裸函数调用: exec(), eval(), open()
            if isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_FUNCTIONS:
                    return False, f"禁止调用的函数: {node.func.id}()"

            # 属性访问调用: os.system(), subprocess.call()
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    module_name = node.func.value.id
                    func_name = node.func.attr
                    if (module_name, func_name) in FORBIDDEN_ATTRIBUTE_CALLS:
                        return False, f"禁止调用的函数: {module_name}.{func_name}()"

    return True, ""

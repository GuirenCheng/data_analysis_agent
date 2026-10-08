"""AST 安全检查器测试。"""

import pytest

from daa.core.safety import check_code_safety


def test_safe_code_passes():
    """安全的代码应该通过检查。"""
    is_safe, msg = check_code_safety("import pandas as pd\nimport numpy as np\nprint('hello')")
    assert is_safe
    assert msg == ""


def test_forbidden_import_blocked():
    """禁止的模块导入应该被阻止。"""
    is_safe, msg = check_code_safety("import subprocess")
    assert not is_safe
    assert "subprocess" in msg


def test_forbidden_function_blocked():
    """禁止的函数调用应该被阻止。"""
    is_safe, msg = check_code_safety("eval('1+1')")
    assert not is_safe
    assert "eval" in msg


def test_exec_blocked():
    """exec() 应该被阻止。"""
    is_safe, msg = check_code_safety("exec('print(1)')")
    assert not is_safe


def test_open_blocked():
    """open() 应该被阻止。"""
    is_safe, msg = check_code_safety("open('/etc/passwd')")
    assert not is_safe


def test_os_system_blocked():
    """os.system() 应该被阻止（修复的漏洞）。"""
    is_safe, msg = check_code_safety("import os\nos.system('ls')")
    assert not is_safe
    assert "os.system" in msg


def test_subprocess_call_blocked():
    """subprocess.call() 应该被阻止。"""
    is_safe, msg = check_code_safety("import subprocess\nsubprocess.call(['ls'])")
    assert not is_safe
    assert "subprocess" in msg


def test_pandas_import_allowed():
    """标准数据分析库应该允许。"""
    is_safe, msg = check_code_safety(
        "import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport duckdb"
    )
    assert is_safe


def test_syntax_error_handled():
    """语法错误的代码应该被捕获。"""
    is_safe, msg = check_code_safety("def broken(")
    assert not is_safe
    assert "语法错误" in msg


def test_duckdb_query_allowed():
    """DuckDB 查询应该被允许。"""
    code = """
import duckdb
result = duckdb.query("SELECT 1").fetchall()
print(result)
"""
    is_safe, msg = check_code_safety(code)
    assert is_safe

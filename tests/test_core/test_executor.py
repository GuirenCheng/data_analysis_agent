"""CodeExecutor 测试。"""

import pytest

from daa.core.executor import CodeExecutor


@pytest.fixture
def executor(tmp_path):
    """创建临时目录中的执行器。"""
    return CodeExecutor(str(tmp_path / "output"))


def test_execute_simple_code(executor):
    """执行简单的 Python 代码。"""
    result = executor.execute_code("print('hello world')")
    assert result["success"]
    assert "hello world" in result["output"]


def test_execute_pandas(executor):
    """执行 pandas 代码，DataFrame 返回值应被格式化为表格。"""
    code = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
df
"""
    result = executor.execute_code(code)
    assert result["success"]
    assert "3行" in result["output"]


def test_execute_unsafe_code(executor):
    """不安全代码应该被阻止。"""
    result = executor.execute_code("eval('1+1')")
    assert not result["success"]
    assert "安全检查" in result["error"]


def test_variable_persistence(executor):
    """变量应在多次执行间保持。"""
    executor.execute_code("x = 42")
    result = executor.execute_code("print(x)")
    assert result["success"]
    assert "42" in result["output"]


def test_error_handling(executor):
    """执行错误应该被捕获。"""
    result = executor.execute_code("1/0")
    assert not result["success"]
    assert "ZeroDivisionError" in result["error"]


def test_environment_info(executor):
    """环境信息应正确返回。"""
    info = executor.get_environment_info()
    assert "pandas" in info.lower() or "matplotlib" in info.lower()


def test_reset_environment(executor):
    """重置应清除变量。"""
    executor.execute_code("x = 42")
    executor.reset_environment()
    # 重置后 x 不应存在
    result = executor.execute_code("print(x)")
    assert not result["success"]

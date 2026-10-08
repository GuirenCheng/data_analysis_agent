"""YAML 协议解析器测试。"""

import pytest

from daa.core.protocol import (
    extract_code_from_response,
    extract_yaml_from_response,
    parse_yaml_response,
)


def test_parse_yaml_with_fence():
    """解析 ```yaml 围栏包围的 YAML。"""
    response = """```yaml
action: "generate_code"
code: |
  print("hello")
reasoning: "test"
```"""
    data = parse_yaml_response(response)
    assert data["action"] == "generate_code"
    assert "print" in data["code"]


def test_parse_yaml_without_fence():
    """解析纯 YAML 文本。"""
    response = """action: "analysis_complete"
final_report: "分析完成" """
    data = parse_yaml_response(response)
    assert data["action"] == "analysis_complete"


def test_extract_code_from_yaml():
    """从 YAML 的 code 字段提取代码。"""
    response = """```yaml
action: "generate_code"
code: |
  import pandas as pd
  df = pd.read_csv('data.csv')
  print(df.head())
```"""
    code = extract_code_from_response(response)
    assert code is not None
    assert "import pandas as pd" in code
    assert "pd.read_csv" in code


def test_extract_code_from_python_fence():
    """从 ```python 围栏提取代码。"""
    response = """```python
import numpy as np
arr = np.array([1, 2, 3])
print(arr)
```"""
    code = extract_code_from_response(response)
    assert code is not None
    assert "import numpy as np" in code


def test_extract_code_from_generic_fence():
    """从通用 ``` 围栏提取代码。"""
    response = """```
import matplotlib.pyplot as plt
plt.figure()
plt.savefig('test.png')
```"""
    code = extract_code_from_response(response)
    assert code is not None
    assert "plt.figure" in code


def test_extract_yaml_basic():
    """基本 YAML 提取。"""
    response = """```yaml
key: value
list:
  - a
  - b
```"""
    yaml_content = extract_yaml_from_response(response)
    assert "key: value" in yaml_content

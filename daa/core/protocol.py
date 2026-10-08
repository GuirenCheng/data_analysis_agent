"""统一的 YAML 响应解析和代码提取 — 消除原始代码中的重复逻辑。"""

import re
from typing import Any, Optional

import yaml


def extract_yaml_from_response(response: str) -> str:
    """从 LLM 响应中提取 YAML 内容。

    尝试顺序: ```yaml 围栏 → ``` 围栏 → 纯文本

    注意: LLM 长输出时经常漏掉闭合围栏（尤其生成最终报告时），因此闭合围栏是
    可选的——用 `$` 锚定到字符串末尾作为兜底，同时把闭合围栏锚定到末尾，避免
    把报告正文里缩进的代码围栏误当成外层闭合围栏。
    """
    if "```yaml" in response:
        pattern = r"```yaml[ \t]*\n(.*?)(?:\n[ \t]*```[ \t]*$|$)"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

    if "```" in response:
        pattern = r"```[ \t]*\n(.*?)(?:\n[ \t]*```[ \t]*$|$)"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

    return response.strip()


def parse_yaml_response(response: str) -> dict[str, Any]:
    """解析 LLM 响应中的 YAML 数据。

    统一了原始 LLMHelper.parse_yaml_response() 和 extract_code_from_response()
    中的重复逻辑。
    """
    try:
        yaml_content = extract_yaml_from_response(response)
        data = yaml.safe_load(yaml_content)
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}


def extract_code_from_response(response: str) -> Optional[str]:
    """从 LLM 响应中提取 Python 代码。

    优先级:
    1. YAML 中的 code 字段
    2. ```python 代码围栏
    3. ``` 通用围栏
    """
    # 首先尝试从 YAML 中提取
    yaml_data = parse_yaml_response(response)
    if yaml_data and "code" in yaml_data:
        code = yaml_data["code"]
        if code and isinstance(code, str) and code.strip():
            return code.strip()

    # 回退到代码围栏提取
    if "```python" in response:
        pattern = r"```python\s*\n(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

    if "```" in response:
        pattern = r"```\s*\n(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            code = match.group(1).strip()
            # 简单判断是否为代码（包含关键字）
            if any(kw in code for kw in ("import ", "def ", "class ", "print(", "df.", "plt.")):
                return code

    return None


def extract_action(response: str) -> str:
    """从响应中提取动作类型。"""
    yaml_data = parse_yaml_response(response)
    return yaml_data.get("action", "generate_code")

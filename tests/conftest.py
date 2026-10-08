"""Pytest 配置和共享 fixtures。"""

import os
import sys
from pathlib import Path

# ── 关键：将项目根目录插入 sys.path 最前面，防止 Desktop/app.py 冲突 ──
_PROJECT_ROOT = str(Path(__file__).parent.parent.resolve())
# 移除可能冲突的父目录
_desktop = str(Path(_PROJECT_ROOT).parent)
if _desktop in sys.path:
    sys.path.remove(_desktop)
# 确保项目根目录在最前面
if _PROJECT_ROOT in sys.path:
    sys.path.remove(_PROJECT_ROOT)
sys.path.insert(0, _PROJECT_ROOT)

import pytest


@pytest.fixture(scope="session")
def test_output_dir(tmp_path_factory) -> Path:
    """测试用的临时输出目录。"""
    return tmp_path_factory.mktemp("test_outputs")


@pytest.fixture
def sample_csv_path(tmp_path) -> Path:
    """创建测试用的 CSV 文件。"""
    csv_content = """date,revenue,cost,profit
2024-01-01,1000,800,200
2024-02-01,1200,900,300
2024-03-01,1100,850,250
2024-04-01,1300,950,350
2024-05-01,1400,1000,400
"""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(csv_content, encoding="utf-8")
    return csv_file

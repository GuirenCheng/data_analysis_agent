"""执行器注册表 — 在 LangGraph 节点间持久化 CodeExecutor 实例。

由于 IPython InteractiveShell 不可序列化，不能存储在 LangGraph checkpoint 中，
使用此注册表在内存中管理执行器实例，按 session_output_dir 索引。
"""

from daa.core.executor import CodeExecutor

_registry: dict[str, CodeExecutor] = {}


def get_or_create_executor(session_output_dir: str) -> CodeExecutor:
    """获取或创建指定会话目录的 CodeExecutor。

    如果该目录的执行器已存在（同一会话的不同节点），直接返回；
    否则创建新的执行器实例。

    Args:
        session_output_dir: 会话输出目录路径

    Returns:
        CodeExecutor 实例
    """
    if session_output_dir not in _registry:
        _registry[session_output_dir] = CodeExecutor(session_output_dir)
        _registry[session_output_dir].set_variable("session_output_dir", session_output_dir)
    return _registry[session_output_dir]


def get_executor(session_output_dir: str) -> CodeExecutor | None:
    """获取已存在的执行器，如果不存在返回 None。"""
    return _registry.get(session_output_dir)


def remove_executor(session_output_dir: str) -> None:
    """移除并重置指定会话的执行器。"""
    executor = _registry.pop(session_output_dir, None)
    if executor:
        executor.reset_environment()


def reset_all() -> None:
    """重置所有执行器（用于测试/关闭）。"""
    for executor in _registry.values():
        executor.reset_environment()
    _registry.clear()

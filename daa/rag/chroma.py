"""共享 ChromaDB 客户端 — 进程级单例，避免每次检索/索引请求重建连接。"""

from functools import lru_cache


@lru_cache()
def get_chroma_client():
    """返回进程级共享的 ChromaDB PersistentClient。

    首次调用时初始化并缓存；后续调用复用同一客户端，
    避免每个请求都重新打开 sqlite / 重建 HNSW 索引带来的冷启动开销。
    """
    import chromadb

    from daa.settings import get_settings

    return chromadb.PersistentClient(path=get_settings().CHROMA_PERSIST_DIR)

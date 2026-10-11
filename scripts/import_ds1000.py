#!/usr/bin/env python3
"""把 DS-1000 数据科学问题导入 RAG 检索库（ChromaDB）。

将 DS-1000 的「问题描述 → query」「参考代码 → code」批量嵌入后，写入
analysis_queries / analysis_code 两个 ChromaDB 集合，挂到指定用户下，
用于扩充知识搜索语料、验证召回效果。

数据文件为 https://github.com/xlang-ai/DS-1000 的 data/ds1000.jsonl.gz，
解压后每行一个 JSON，字段：prompt / reference_code / metadata / code_context。

用法:
    .venv/Scripts/python.exe scripts/import_ds1000.py \
        --data data/ds1000/ds1000.jsonl \
        --user-id 7c8765be-38f9-473c-90b7-99a09d6fbf46 \
        [--limit 0] [--batch-size 64]
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# 修复 Windows 控制台 GBK 编码无法输出 emoji 的问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from daa.rag.chroma import get_chroma_client
from daa.rag.embedder import Embedder

# content_type → ChromaDB 集合名（须与 daa/rag/indexer.py、retriever.py 一致）
COLLECTIONS = {
    "query": "analysis_queries",
    "code": "analysis_code",
}


def load_problems(path: Path, limit: int) -> list[dict]:
    """读取 DS-1000 JSONL，返回问题列表（受 limit 限制，0 表示全部）。"""
    problems: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            problems.append(json.loads(line))
            if limit and len(problems) >= limit:
                break
    return problems


def clean_query(prompt: str) -> str:
    """去掉 DS-1000 prompt 里的 "Problem:" 前缀，只保留自然描述。"""
    text = prompt.strip()
    if text.startswith("Problem:"):
        text = text[len("Problem:"):].strip()
    return text


def _upsert_batch(collection, embedder, batch_size, ids, texts, metadatas) -> int:
    """分批嵌入并 upsert 到集合，返回写入条数。"""
    n = 0
    for start in range(0, len(texts), batch_size):
        chunk_ids = ids[start:start + batch_size]
        chunk_texts = texts[start:start + batch_size]
        chunk_metas = metadatas[start:start + batch_size]
        embeddings = embedder.embed_texts(chunk_texts)
        collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=chunk_metas,
        )
        n += len(chunk_texts)
        print(f"  已写入 {n}/{len(texts)} 条")
    return n


async def main() -> None:
    parser = argparse.ArgumentParser(description="导入 DS-1000 到 RAG 检索库")
    parser.add_argument("--data", required=True, help="DS-1000 JSONL 文件路径")
    parser.add_argument("--user-id", required=True, help="目标用户 ID（检索按 user_id 隔离）")
    parser.add_argument("--limit", type=int, default=0, help="最多导入条数，0 表示全部")
    parser.add_argument("--batch-size", type=int, default=64, help="每次 embedding 的批量大小")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"❌ 未找到数据文件: {data_path}")
        sys.exit(1)

    problems = load_problems(data_path, args.limit)
    if not problems:
        print("❌ 数据文件为空")
        sys.exit(1)
    print(f"📥 加载 {len(problems)} 条 DS-1000 问题")

    client = get_chroma_client()
    embedder = Embedder()

    query_collection = client.get_or_create_collection(
        name=COLLECTIONS["query"], metadata={"hnsw:space": "cosine"}
    )
    code_collection = client.get_or_create_collection(
        name=COLLECTIONS["code"], metadata={"hnsw:space": "cosine"}
    )

    # 组装待索引内容
    query_ids, query_texts, query_metas = [], [], []
    code_ids, code_texts, code_metas = [], [], []

    for p in problems:
        pid = p["metadata"]["problem_id"]
        lib = p["metadata"]["library"]
        base_meta = {
            "user_id": args.user_id,
            "source_session_id": f"ds1000-{pid}",
            "library": lib,
        }

        query_ids.append(f"ds1000-{pid}-query")
        query_texts.append(clean_query(p["prompt"]))
        query_metas.append({**base_meta, "content_type": "query"})

        code_ids.append(f"ds1000-{pid}-code")
        code_texts.append(p["reference_code"])
        code_metas.append({**base_meta, "content_type": "code"})

    print(f"🔤 开始嵌入并写入「query」集合 ({len(query_texts)} 条)...")
    _upsert_batch(query_collection, embedder, args.batch_size, query_ids, query_texts, query_metas)

    print(f"🔤 开始嵌入并写入「code」集合 ({len(code_texts)} 条)...")
    _upsert_batch(code_collection, embedder, args.batch_size, code_ids, code_texts, code_metas)

    print(f"\n✅ 完成：共写入 query {len(query_texts)} 条、code {len(code_texts)} 条")


if __name__ == "__main__":
    asyncio.run(main())

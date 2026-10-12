#!/usr/bin/env python3
"""RAG 检索质量评测 — 基于 DS-1000 的自动标注（Recall@k / MRR@k）。

DS-1000 每个问题天然是「题目(prompt) → 参考代码(reference_code)」配对：
- 查询 = 某个问题的 prompt（已入库 analysis_queries）
- 正确答案 = 该问题自己的参考代码（已入库 analysis_code，source_session_id = ds1000-{pid}）

因此无需人工标注即可全自动计算 Recall@k / MRR：抽样 N 个问题 → 拿 prompt 去
检索 analysis_code → 检查对应 ds1000-{pid}-code 是否出现在前 k 条。

主指标 Recall@5（进没进最终给 LLM 的那几条），辅助指标 MRR（相关结果排第几）。

⚠️ 注意：DS-1000 是「代码生成」数据集而非「检索」数据集——1000 个问题几乎都是
「操作 pandas/numpy/torch 的 DataFrame/tensor」，正确答案与其它代码高度雷同，
「精确命中那一条 reference_code」本身是病态任务，实测 Recall@k 普遍为 0。
因此本脚本更适合作为评测框架：它把 Recall@k / MRR 的度量逻辑做对了，
要得到对真实业务有意义的 recall，应改用人工标注的中文评测集（query → 相关文档）。

用法:
    .venv/Scripts/python.exe scripts/eval_rag.py \
        --user-id 7c8765be-38f9-473c-90b7-99a09d6fbf46 \
        [--sample 200] [--seed 42] [--rerank both] [--top-k 10] [--threshold 0.3]
"""

import argparse
import asyncio
import random
import sys
import time
from pathlib import Path

# 修复 Windows 控制台 GBK 编码无法输出中文/emoji 的问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from daa.rag.chroma import get_chroma_client
from daa.rag.embedder import EmbeddingUnavailableError
from daa.rag.retriever import RAGRetriever
from daa.settings import get_settings

# 报告的命中档位（Recall@k）
KS = (1, 3, 5, 10)


def load_ds1000_queries(client, user_id: str) -> list[tuple[str, str]]:
    """从 analysis_queries 读取 DS-1000 问题，返回 (prompt, source_session_id) 列表。"""
    try:
        col = client.get_collection("analysis_queries")
    except Exception as e:
        print(f"❌ 无法获取 analysis_queries 集合: {e}")
        return []
    res = col.get(where={"user_id": user_id}, include=["documents", "metadatas"])
    queries: list[tuple[str, str]] = []
    for i in range(len(res["ids"])):
        if res["ids"][i].endswith("-query"):
            meta = res["metadatas"][i] or {}
            queries.append((res["documents"][i], meta.get("source_session_id", "")))
    return queries


def find_rank(results, correct_sid: str):
    """返回正确文档在结果中的 1-based 排名，未命中返回 None。"""
    for i, ctx in enumerate(results, 1):
        if ctx.metadata.get("source_session_id") == correct_sid:
            return i
    return None


async def run_eval(retriever, user_id: str, samples, max_k: int) -> dict:
    """跑一轮评测，返回 {n, recall: {k: hit率}, mrr}。"""
    hits = {k: 0 for k in KS}
    rr_sum = 0.0
    n = 0
    for prompt, sid in samples:
        results = await retriever.retrieve_context(
            user_id=user_id,
            current_query=prompt,
            top_k=max_k,
            content_types=["code"],
        )
        rank = find_rank(results, sid)
        n += 1
        if rank is not None:
            for k in KS:
                if rank <= k:
                    hits[k] += 1
            rr_sum += 1.0 / rank
        if n % 50 == 0:
            print(f"    已评测 {n}/{len(samples)} ...")
    return {
        "n": n,
        "recall": {k: hits[k] / n for k in KS},
        "mrr": rr_sum / n,
    }


def print_table(max_k: int, results: dict[str, dict]) -> None:
    """打印各模式对比表。"""
    labels = list(results.keys())
    n = results[labels[0]]["n"]
    shown_ks = [k for k in KS if k <= max_k]

    print("\n" + "═" * 62)
    print(f"样本 {n} 条 | 检索范围=code | top_k={max_k}")
    print("─" * 62)
    print("指标        " + "".join(f"{label:>14}" for label in labels))
    print("─" * 62)
    for k in shown_ks:
        row = f"Recall@{k:<3}   " + "".join(
            f"{results[label]['recall'][k] * 100:>13.1f}%" for label in labels
        )
        if k == 5:
            row += "   ← 主指标"
        print(row)
    mrr_row = f"MRR@{max_k:<3}     " + "".join(
        f"{results[label]['mrr']:>14.3f}" for label in labels
    )
    print(mrr_row + "   ← 辅助指标")
    print("═" * 62)


async def main() -> None:
    parser = argparse.ArgumentParser(description="DS-1000 RAG 检索质量评测（Recall@k / MRR）")
    parser.add_argument("--user-id", required=True, help="DS-1000 数据所属用户 ID")
    parser.add_argument("--sample", type=int, default=200, help="抽样评测的问题数，0=全部")
    parser.add_argument("--seed", type=int, default=42, help="随机种子（保证可复现）")
    parser.add_argument("--rerank", choices=["on", "off", "both"], default="both",
                        help="rerank 开关对比（默认 both）")
    parser.add_argument("--top-k", type=int, default=10,
                        help="检索的最大 k，报告 Recall@1/3/5/10 与 MRR@k")
    parser.add_argument("--threshold", type=float, default=None,
                        help="覆盖 RERANK_THRESHOLD（默认读 .env/settings）")
    args = parser.parse_args()

    settings = get_settings()
    if args.threshold is not None:
        settings.RERANK_THRESHOLD = args.threshold

    client = get_chroma_client()
    queries = load_ds1000_queries(client, args.user_id)
    if not queries:
        print("❌ 该用户下未找到 DS-1000 query 数据（id 以 -query 结尾）")
        print("   请确认 DS-1000 已导入到该用户（参考 scripts/import_ds1000.py）")
        sys.exit(1)

    random.seed(args.seed)
    n_sample = len(queries) if args.sample == 0 else min(args.sample, len(queries))
    sampled = random.sample(queries, n_sample)
    print(f"📥 加载 {len(queries)} 个 DS-1000 问题，抽样 {n_sample} 个（seed={args.seed}）")

    retriever = RAGRetriever()
    modes: list[tuple[str, bool]] = []
    if args.rerank in ("on", "both"):
        modes.append(("rerank=on", True))
    if args.rerank in ("off", "both"):
        modes.append(("rerank=off", False))

    results: dict[str, dict] = {}
    for label, enabled in modes:
        settings.RERANK_ENABLED = enabled
        print(f"\n>>> 评测 {label} ...")
        t0 = time.time()
        try:
            results[label] = await run_eval(retriever, args.user_id, sampled, args.top_k)
        except EmbeddingUnavailableError as e:
            print(f"❌ 向量嵌入服务不可用，评测中止: {e}")
            sys.exit(1)
        print(f"    完成，耗时 {time.time() - t0:.1f}s")

    print_table(args.top_k, results)


if __name__ == "__main__":
    asyncio.run(main())

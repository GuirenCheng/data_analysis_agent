"""文本分块策略 — 为 RAG 索引做文档切分。"""

import re

from daa.settings import get_settings


class TextSplitter:
    """智能文本分块器。

    支持不同内容类型的切分策略:
    - report: 按 Markdown 标题 + 段落切分
    - code: 按逻辑块（空行分隔）切分
    - query: 全文本嵌入，不切分
    """

    def __init__(self):
        settings = get_settings()
        self.chunk_size = settings.RAG_CHUNK_SIZE
        self.chunk_overlap = settings.RAG_CHUNK_OVERLAP

    def split_report(self, text: str) -> list[str]:
        """按 Markdown 标题和字符数切分报告。

        优先在 ## 边界切分，超过 chunk_size 的段落二次切分。
        """
        # 按 ## 标题切分
        sections = re.split(r"\n(?=## )", text)
        chunks: list[str] = []

        for section in sections:
            if len(section) <= self.chunk_size:
                chunks.append(section.strip())
            else:
                # 二次切分：按段落
                paragraphs = section.split("\n\n")
                current_chunk = ""
                for para in paragraphs:
                    if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                        chunks.append(current_chunk.strip())
                        # 重叠
                        overlap_text = current_chunk[-self.chunk_overlap:] if self.chunk_overlap else ""
                        current_chunk = overlap_text + "\n\n" + para
                    else:
                        current_chunk += ("\n\n" + para) if current_chunk else para
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

        return [c for c in chunks if c]

    def split_code(self, text: str) -> list[str]:
        """按逻辑块切分代码。

        以连续的空行为分隔符（函数/类之间的间隔）。
        """
        # 按双空行分隔
        blocks = re.split(r"\n\n\n+", text)
        chunks: list[str] = []
        current_chunk = ""

        for block in blocks:
            if len(current_chunk) + len(block) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = block
            else:
                current_chunk += ("\n\n\n" + block) if current_chunk else block

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return [c for c in chunks if c]

    def split_query(self, text: str) -> list[str]:
        """查询文本直接全量嵌入，不切分。"""
        return [text.strip()]

"""System prompt and context formatting for RAG answers (bilingual zh/en)."""
from __future__ import annotations

from .retriever import RetrievedChunk

SYSTEM_PROMPT = """\
You are a bilingual (中文/English) home-appliance manual assistant.

Rules:
- Answer ONLY from the provided manual excerpts. If the excerpts do not contain
  the answer, say you cannot find it in the manual and suggest what to check —
  do not invent steps.
- Reply in the same language the user used (中文问就用中文答).
- Be concise and practical: give the actual steps to use or fix the device.
- Cite the excerpt numbers you relied on, e.g. “(来源 1, 3)”.
"""


def format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "（没有检索到相关说明书内容 / No relevant manual excerpts found.）"
    lines: list[str] = []
    for i, c in enumerate(chunks, start=1):
        snippet = c.text.strip().replace("\n", " ")
        lines.append(f"[来源 {i} | 第 {c.page} 页 / page {c.page}]\n{snippet}")
    return "\n\n".join(lines)

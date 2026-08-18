"""轻量设计文档检索：按章节分块 + 关键词打分

为什么不用向量库？
- 启动阶段先跑通一条链，避免引入 ChromaDB 等重量依赖；
- 设计文档规模小（~5KB），章节级关键词检索足够准；
- 每个检索步骤都能讲清楚原理，方便面试时解释。
"""
import re

from . import config

# 章节标题行：中文数字 + "、"（如"一、游戏概述"）或分隔线
_SECTION_RE = re.compile(r"^\s*[一二三四五六七八九十]+、")
_DIVIDER_RE = re.compile(r"^\s*=+\s*$")

# 常见停用词（中文 2 字无意义词 + 英文虚词）
_STOPWORDS = {
    "一个", "这个", "那个", "可以", "进行", "以及", "或者", "需要", "通过",
    "the", "and", "for", "with", "from", "that", "this", "into", "have",
    "level", "game", "player", "design",
}


def load_blocks() -> list[str]:
    """读取设计文档并按章节切块"""
    text = config.DESIGN_DOC_PATH.read_text(encoding="utf-8")
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if _SECTION_RE.match(line) or _DIVIDER_RE.match(line):
            if current:
                blocks.append("\n".join(current))
                current = []
        current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def _extract_keywords(level_description: str) -> list[str]:
    """从关卡描述中提取检索关键词（中文 2+ 字词 / 英文单词 / 数字）"""
    tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]+|\d+(?:\.\d+)?", level_description)
    return [t for t in tokens if t.lower() not in _STOPWORDS]


def _score(block: str, keywords: list[str]) -> int:
    return sum(block.count(k) for k in keywords)


def retrieve_design_sections(level_description: str, top_k: int | None = None) -> str:
    """按关键词从设计文档中检索最相关的 top_k 个章节片段"""
    blocks = load_blocks()
    keywords = _extract_keywords(level_description)
    if not keywords:
        return "\n".join(blocks[:3])  # 无有效关键词时返回开头章节兜底
    scored = sorted(
        blocks, key=lambda b: _score(b, keywords), reverse=True
    )
    top = scored[: top_k or config.RETRIEVAL_TOP_K]
    return "\n\n----\n\n".join(top)

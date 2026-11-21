"""Markdown layout generation."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from .ocr import OCRWord
from .table import TableBlock


@dataclass
class MarkdownBlock:
    y: float
    x: float
    content: str


def build_page_markdown(page_no: int, words: list[OCRWord], tables: list[TableBlock]) -> str:
    blocks: list[MarkdownBlock] = [
        MarkdownBlock(y=table.bbox[1], x=table.bbox[0], content=table.markdown) for table in tables
    ]

    table_boxes = [table.bbox for table in tables]
    text_words = [word for word in words if not _inside_any_table(word, table_boxes)]
    blocks.extend(_words_to_line_blocks(text_words))

    lines = [f"## 第{page_no}页"]
    if blocks:
        for block in sorted(blocks, key=lambda item: (item.y, item.x)):
            if block.content.strip():
                lines.extend(["", block.content.strip()])
    else:
        lines.extend(["", "（本页未识别到内容）"])
    return "\n".join(lines).strip()


def _words_to_line_blocks(words: list[OCRWord]) -> list[MarkdownBlock]:
    if not words:
        return []

    heights = [word.height for word in words]
    tolerance = max(10.0, median(heights) * 0.75)
    lines: list[list[OCRWord]] = []

    for word in sorted(words, key=lambda item: (item.center[1], item.bbox[0])):
        if not lines:
            lines.append([word])
            continue
        last_center = sum(item.center[1] for item in lines[-1]) / len(lines[-1])
        if abs(word.center[1] - last_center) <= tolerance:
            lines[-1].append(word)
        else:
            lines.append([word])

    blocks: list[MarkdownBlock] = []
    for line_words in lines:
        sorted_words = sorted(line_words, key=lambda item: item.bbox[0])
        text = " ".join(item.text for item in sorted_words).strip()
        if text:
            blocks.append(MarkdownBlock(y=min(item.bbox[1] for item in line_words), x=min(item.bbox[0] for item in line_words), content=text))
    return blocks


def _inside_any_table(word: OCRWord, table_boxes: list[tuple[int, int, int, int]]) -> bool:
    cx, cy = word.center
    for x1, y1, x2, y2 in table_boxes:
        if x1 <= cx <= x2 and y1 <= cy <= y2:
            return True
    return False

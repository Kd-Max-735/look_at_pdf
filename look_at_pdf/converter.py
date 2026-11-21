"""Unified conversion entrypoint."""

from __future__ import annotations

from .errors import (
    ERR_BLANK_DOCUMENT,
    ERR_UNKNOWN,
    SUCCESS,
    ConvertError,
)
from .markdown import build_page_markdown
from .ocr import OCRWord, ocr_image
from .preprocess import preprocess_image
from .renderer import render_document
from .schemas import ConvertRequest, ConvertResult, Stat
from .table import detect_tables


def convert_to_markdown(file_path: str, enhance_img: bool = True, fix_table: bool = True) -> dict:
    """Convert a local scanned PDF/image to Markdown.

    The returned dict is intentionally JSON-serializable and is shared by the
    Python API and MCP tool.
    """

    request = ConvertRequest(file_path=file_path, enhance_img=enhance_img, fix_table=fix_table)
    try:
        pages = render_document(request.file_path)
        if not pages:
            raise ConvertError(ERR_BLANK_DOCUMENT)

        markdown_pages: list[str] = []
        all_words: list[OCRWord] = []
        table_num = 0

        for page in pages:
            processed = preprocess_image(page.image, request.enhance_img)
            words = ocr_image(processed)
            tables = detect_tables(processed, words, request.fix_table)
            markdown_pages.append(build_page_markdown(page.page_no, words, tables))
            all_words.extend(words)
            table_num += len(tables)

        if not all_words and table_num == 0:
            raise ConvertError(ERR_BLANK_DOCUMENT)

        avg_accuracy = _avg_accuracy(all_words)
        return ConvertResult(
            code=SUCCESS,
            msg="success",
            md_content="\n\n---\n\n".join(markdown_pages).strip() + "\n",
            stat=Stat(page_num=len(pages), table_num=table_num, avg_accuracy=avg_accuracy),
        ).to_dict()
    except ConvertError as exc:
        return ConvertResult(code=exc.code, msg=str(exc)).to_dict()
    except Exception as exc:  # Last safety net: callers should get a structured error.
        return ConvertResult(code=ERR_UNKNOWN, msg=f"unknown error: {exc}").to_dict()


def _avg_accuracy(words: list[OCRWord]) -> float:
    if not words:
        return 0.0
    return sum(word.confidence for word in words) / len(words) * 100

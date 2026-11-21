"""Line-based table detection and Markdown table rendering."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from .ocr import OCRWord


@dataclass
class TableBlock:
    bbox: tuple[int, int, int, int]
    markdown: str


def detect_tables(image: Image.Image, words: list[OCRWord], fix_table: bool) -> list[TableBlock]:
    try:
        import cv2
        import numpy as np
    except Exception:
        return []

    arr = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    binary = cv2.adaptiveThreshold(
        ~gray,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        15,
        -2,
    )

    height, width = binary.shape[:2]
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(24, width // 30), 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(24, height // 40)))
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel)
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel)
    line_mask = cv2.add(horizontal, vertical)
    connected = cv2.dilate(line_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)), iterations=2)

    contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[tuple[int, int, int, int]] = []
    page_area = width * height
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h < page_area * 0.005:
            continue
        if w < width * 0.18 or h < height * 0.03:
            continue
        candidates.append((x, y, x + w, y + h))

    tables: list[TableBlock] = []
    for bbox in sorted(candidates, key=lambda b: (b[1], b[0])):
        block = _build_table_block(bbox, horizontal, vertical, words, fix_table)
        if block is not None:
            tables.append(block)
    return _dedupe_tables(tables)


def _build_table_block(
    bbox: tuple[int, int, int, int],
    horizontal,
    vertical,
    words: list[OCRWord],
    fix_table: bool,
) -> TableBlock | None:
    try:
        import cv2
    except Exception:
        return None

    x1, y1, x2, y2 = bbox
    roi_h = horizontal[y1:y2, x1:x2]
    roi_v = vertical[y1:y2, x1:x2]

    h_contours, _ = cv2.findContours(roi_h, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    v_contours, _ = cv2.findContours(roi_v, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h_positions = []
    for contour in h_contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w >= max(40, (x2 - x1) * 0.45):
            h_positions.append(y1 + y + h / 2)

    v_positions = []
    for contour in v_contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h >= max(24, (y2 - y1) * 0.45):
            v_positions.append(x1 + x + w / 2)

    h_lines = _merge_positions(h_positions, tolerance=10)
    v_lines = _merge_positions(v_positions, tolerance=10)
    if len(h_lines) < 2 or len(v_lines) < 2:
        return None

    rows: list[list[str]] = []
    for row_idx in range(len(h_lines) - 1):
        row: list[str] = []
        top, bottom = h_lines[row_idx], h_lines[row_idx + 1]
        for col_idx in range(len(v_lines) - 1):
            left, right = v_lines[col_idx], v_lines[col_idx + 1]
            cell_words = [
                word
                for word in words
                if left - 3 <= word.center[0] <= right + 3 and top - 3 <= word.center[1] <= bottom + 3
            ]
            row.append(_join_cell_words(cell_words))
        rows.append(row)

    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        return None

    if fix_table:
        width = max(len(row) for row in rows)
        rows = [row + [""] * (width - len(row)) for row in rows]

    markdown = _rows_to_markdown(rows)
    return TableBlock(bbox=bbox, markdown=markdown)


def _merge_positions(values: list[float], tolerance: int) -> list[int]:
    if not values:
        return []

    merged: list[list[float]] = []
    for value in sorted(values):
        if not merged or abs(value - merged[-1][-1]) > tolerance:
            merged.append([value])
        else:
            merged[-1].append(value)
    return [round(sum(group) / len(group)) for group in merged]


def _join_cell_words(words: list[OCRWord]) -> str:
    if not words:
        return ""
    words = sorted(words, key=lambda w: (w.bbox[1], w.bbox[0]))
    return " ".join(word.text for word in words).strip()


def _rows_to_markdown(rows: list[list[str]]) -> str:
    col_count = max(len(row) for row in rows)
    normalized = [row + [""] * (col_count - len(row)) for row in rows]

    header = normalized[0]
    if not any(cell.strip() for cell in header):
        header = [f"列{i + 1}" for i in range(col_count)]
    body = normalized[1:] or [[""] * col_count]

    lines = [
        "| " + " | ".join(_escape_cell(cell) for cell in header) + " |",
        "| " + " | ".join("---" for _ in range(col_count)) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(_escape_cell(cell) for cell in row) + " |")
    return "\n".join(lines)


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _dedupe_tables(tables: list[TableBlock]) -> list[TableBlock]:
    kept: list[TableBlock] = []
    for table in tables:
        if any(_overlap_ratio(table.bbox, other.bbox) > 0.8 for other in kept):
            continue
        kept.append(table)
    return kept


def _overlap_ratio(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix1 >= ix2 or iy1 >= iy2:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    small = min((ax2 - ax1) * (ay2 - ay1), (bx2 - bx1) * (by2 - by1))
    return inter / max(1, small)

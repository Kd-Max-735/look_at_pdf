"""Create an image-only multi-page sample PDF for demos."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def draw_table(draw: ImageDraw.ImageDraw, x: int, y: int, col_widths: list[int], row_height: int, rows: list[list[str]], font) -> None:
    total_width = sum(col_widths)
    total_height = row_height * len(rows)
    draw.rectangle([x, y, x + total_width, y + total_height], outline="black", width=3)

    current_x = x
    for width in col_widths[:-1]:
        current_x += width
        draw.line([current_x, y, current_x, y + total_height], fill="black", width=3)

    for idx in range(1, len(rows)):
        yy = y + idx * row_height
        draw.line([x, yy, x + total_width, yy], fill="black", width=3)

    for row_idx, row in enumerate(rows):
        current_x = x
        for col_idx, cell in enumerate(row):
            draw.text((current_x + 18, y + row_idx * row_height + 20), cell, font=font, fill="black")
            current_x += col_widths[col_idx]


def page_one() -> Image.Image:
    img = Image.new("RGB", (1654, 2339), "white")
    draw = ImageDraw.Draw(img)
    title = load_font(58)
    body = load_font(38)
    table_font = load_font(34)

    draw.text((150, 130), "扫描合同样例", font=title, fill="black")
    draw.text((150, 250), "本文件用于验证 look_at_pdf 的 OCR、分页和表格 Markdown 输出。", font=body, fill="black")
    draw.text((150, 320), "以下表格必须被转换为标准 Markdown 表格，而不是纯文本。", font=body, fill="black")

    rows = [
        ["项目", "数量", "金额"],
        ["扫描页", "2", "120元"],
        ["表格识别", "1", "80元"],
        ["合计", "3", "200元"],
    ]
    draw_table(draw, 150, 470, [420, 300, 360], 95, rows, table_font)
    draw.text((150, 960), "备注：图像增强开启后，可降低轻微噪声和倾斜造成的识别误差。", font=body, fill="black")
    return img


def page_two() -> Image.Image:
    img = Image.new("RGB", (1654, 2339), "white")
    draw = ImageDraw.Draw(img)
    title = load_font(54)
    body = load_font(38)
    table_font = load_font(34)

    draw.text((150, 140), "第二页", font=title, fill="black")
    draw.text((150, 250), "本页包含验收标准和另一张明细表。", font=body, fill="black")

    rows = [
        ["标准", "目标"],
        ["平均置信度", "90%以上"],
        ["分页标记", "## 第X页"],
        ["输出格式", "Markdown"],
    ]
    draw_table(draw, 150, 410, [520, 520], 95, rows, table_font)
    draw.text((150, 860), "如果文件为空、损坏或加密，程序应返回明确错误码。", font=body, fill="black")
    return img


def main() -> None:
    out_dir = Path("samples")
    out_dir.mkdir(exist_ok=True)
    pages = [page_one(), page_two()]
    pdf_path = out_dir / "sample_scanned.pdf"
    pages[0].save(pdf_path, "PDF", resolution=220, save_all=True, append_images=pages[1:])
    print(pdf_path.resolve())


if __name__ == "__main__":
    main()

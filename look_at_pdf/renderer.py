"""Load PDFs or images and render them as page images."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageSequence, UnidentifiedImageError

from .errors import (
    ERR_DAMAGED_FILE,
    ERR_ENCRYPTED_PDF,
    ERR_FILE_NOT_FOUND,
    ERR_UNSUPPORTED_FILE,
    ConvertError,
)

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


@dataclass
class PageImage:
    page_no: int
    image: Image.Image


def render_document(file_path: str, dpi: int = 220) -> list[PageImage]:
    path = Path(file_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise ConvertError(ERR_FILE_NOT_FOUND, str(path))

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _render_pdf(path, dpi=dpi)
    if suffix in SUPPORTED_IMAGE_SUFFIXES:
        return _load_image(path)
    raise ConvertError(ERR_UNSUPPORTED_FILE, suffix or "missing suffix")


def _render_pdf(path: Path, dpi: int) -> list[PageImage]:
    try:
        import fitz
    except Exception as exc:  # pragma: no cover - environment dependent
        raise ConvertError(ERR_DAMAGED_FILE, f"PyMuPDF import failed: {exc}") from exc

    try:
        doc = fitz.open(path)
    except Exception as exc:
        raise ConvertError(ERR_DAMAGED_FILE, str(exc)) from exc

    try:
        if doc.needs_pass:
            raise ConvertError(ERR_ENCRYPTED_PDF, str(path))

        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        pages: list[PageImage] = []
        for idx, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            pages.append(PageImage(page_no=idx, image=image))
        return pages
    finally:
        doc.close()


def _load_image(path: Path) -> list[PageImage]:
    try:
        image = Image.open(path)
    except (UnidentifiedImageError, OSError) as exc:
        raise ConvertError(ERR_DAMAGED_FILE, str(exc)) from exc

    pages: list[PageImage] = []
    try:
        for idx, frame in enumerate(ImageSequence.Iterator(image), start=1):
            pages.append(PageImage(page_no=idx, image=frame.convert("RGB")))
    finally:
        image.close()
    return pages

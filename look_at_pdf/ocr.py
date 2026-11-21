"""OCR backend adapters."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from PIL import Image

from .errors import ERR_OCR_UNAVAILABLE, ConvertError


@dataclass(frozen=True)
class OCRWord:
    text: str
    confidence: float
    bbox: tuple[float, float, float, float]

    @property
    def center(self) -> tuple[float, float]:
        left, top, right, bottom = self.bbox
        return ((left + right) / 2, (top + bottom) / 2)

    @property
    def height(self) -> float:
        return max(1.0, self.bbox[3] - self.bbox[1])


def ocr_image(image: Image.Image) -> list[OCRWord]:
    engine = _get_rapidocr()
    try:
        import numpy as np

        result, _ = engine(np.array(image.convert("RGB")))
    except ConvertError:
        raise
    except Exception as exc:
        raise ConvertError(ERR_OCR_UNAVAILABLE, str(exc)) from exc

    words: list[OCRWord] = []
    for item in result or []:
        parsed = _parse_rapidocr_item(item)
        if parsed is not None:
            words.append(parsed)
    return words


@lru_cache(maxsize=1)
def _get_rapidocr():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception as exc:
        raise ConvertError(
            ERR_OCR_UNAVAILABLE,
            "install rapidocr-onnxruntime or run `pip install -r requirements.txt`",
        ) from exc
    return RapidOCR()


def _parse_rapidocr_item(item) -> OCRWord | None:
    if len(item) < 3:
        return None

    box, text, score = item[0], str(item[1]).strip(), float(item[2])
    if not text:
        return None

    xs = [float(point[0]) for point in box]
    ys = [float(point[1]) for point in box]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    return OCRWord(text=text, confidence=max(0.0, min(1.0, score)), bbox=bbox)

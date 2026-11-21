"""Image enhancement for scanned pages."""

from __future__ import annotations

from PIL import Image, ImageOps


def preprocess_image(image: Image.Image, enhance_img: bool) -> Image.Image:
    rgb = image.convert("RGB")
    if not enhance_img:
        return rgb

    try:
        import cv2
        import numpy as np
    except Exception:
        return ImageOps.autocontrast(rgb.convert("L")).convert("RGB")

    arr = np.array(rgb)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, None, h=8, templateWindowSize=7, searchWindowSize=21)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)

    rotated = _deskew(gray, cv2, np)
    return Image.fromarray(rotated).convert("RGB")


def _deskew(gray, cv2, np):
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(binary > 0))
    if coords.size == 0:
        return gray

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) < 0.2 or abs(angle) > 12:
        return gray

    h, w = gray.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(gray, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

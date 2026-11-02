from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass

import cv2
import numpy as np
import requests

from config import VEHICLE_LOOKUP_URL
from core import database as db

log = logging.getLogger(__name__)

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_PLATE_KEEP = re.compile(r"[^A-Z0-9\u0600-\u06FF]")


def normalize_plate(text: str) -> str:
    text = (text or "").translate(_ARABIC_DIGITS).upper()
    text = re.sub(r"\s+", "", text)
    text = _PLATE_KEEP.sub("", text)
    return text[:12]


def format_plate(text: str) -> str:
    text = normalize_plate(text)
    if len(text) > 5:
        return f"{text[:3]}-{text[3:]}"
    return text


@dataclass
class PlateReading:
    text: str
    confidence: float
    box: tuple[int, int, int, int]
    crop: np.ndarray | None = None


class PlateEngine:
    def __init__(self) -> None:
        self._ocr = None
        self._lock = threading.RLock()
        self.enabled = db.get_bool_setting("plate_recognition", True)

    def _get_ocr(self):
        if self._ocr is None:
            with self._lock:
                if self._ocr is None:
                    from rapidocr_onnxruntime import RapidOCR

                    self._ocr = RapidOCR()
        return self._ocr

    @staticmethod
    def _ocr_items(result) -> list[tuple[str, float]]:
        items: list[tuple[str, float]] = []
        if result is None:
            return items
        txts = getattr(result, "txts", None)
        scores = getattr(result, "scores", None)
        if txts is not None:
            for text, score in zip(txts, scores or []):
                items.append((str(text), float(score)))
            return items
        try:
            for entry in result:
                if not entry or len(entry) < 3:
                    continue
                text = str(entry[1])
                score = float(entry[2])
                items.append((text, score))
        except (TypeError, ValueError):
            pass
        return items

    def _read_crop(self, crop: np.ndarray) -> tuple[str, float]:
        if crop.size == 0:
            return "", 0.0
        h, w = crop.shape[:2]
        scale = max(1.0, 90.0 / max(1, h))
        if scale > 1.0:
            crop = cv2.resize(crop, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
        try:
            ocr = self._get_ocr()
            result, _ = ocr(crop)
        except Exception as exc:  # noqa: BLE001
            log.debug("OCR failed: %s", exc)
            return "", 0.0
        items = self._ocr_items(result)
        if not items:
            return "", 0.0
        items.sort(key=lambda item: (-item[1], item[0]))
        best_text = ""
        best_score = 0.0
        for text, score in items:
            cleaned = normalize_plate(text)
            alnum = len(re.findall(r"[A-Z0-9\u0600-\u06FF]", cleaned))
            if alnum < 3:
                continue
            if score > best_score:
                best_text, best_score = cleaned, score
        return best_text, best_score

    @staticmethod
    def _plate_candidates(image: np.ndarray, min_width: int = 70) -> list[np.ndarray]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        edges = cv2.Canny(gray, 60, 180)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: list[tuple[float, np.ndarray, int, int, int, int]] = []
        img_h, img_w = image.shape[:2]
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w < min_width or h < 16 or w > img_w * 0.98 or h > img_h * 0.5:
                continue
            ratio = w / float(h)
            if not 1.6 <= ratio <= 7.5:
                continue
            area = cv2.contourArea(contour)
            if area < 700 or area < w * h * 0.3:
                continue
            aspect_bonus = min(ratio, 5.5)
            score = area * 0.01 + aspect_bonus * 50
            candidates.append((score, contour, x, y, w, h))
        candidates.sort(key=lambda item: item[0], reverse=True)
        crops = []
        for _, contour, x, y, w, h in candidates[:5]:
            pad_x, pad_y = max(2, int(w * 0.04)), max(2, int(h * 0.12))
            x1, y1 = max(0, x - pad_x), max(0, y - pad_y)
            x2, y2 = min(img_w, x + w + pad_x), min(img_h, y + h + pad_y)
            crop = image[y1:y2, x1:x2].copy()
            if crop.size == 0:
                continue
            rect = cv2.minAreaRect(contour)
            if rect[1][0] > 0 and rect[1][1] > 0:
                box = cv2.boxPoints(rect)
                width = int(max(rect[1]))
                height = int(min(rect[1]))
                if height > 8 and width > min_width:
                    src = cv2.boxPoints(rect).astype(np.float32)
                    dst = np.array([[0, 0], [width, 0], [width, height], [0, height]], dtype=np.float32)
                    try:
                        matrix = cv2.getPerspectiveTransform(src, dst)
                        crop = cv2.warpPerspective(image, matrix, (width, height))
                    except cv2.error:
                        pass
            crops.append(crop)
        return crops

    def scan(self, image: np.ndarray, max_candidates: int = 3) -> list[PlateReading]:
        if image is None or image.size == 0:
            return []
        readings: list[PlateReading] = []
        crops = self._plate_candidates(image)
        if not crops:
            height = image.shape[0]
            crops = [image[int(height * 0.45) :, :]]
        for crop in crops[:max_candidates]:
            text, score = self._read_crop(crop)
            if len(text) < 4 or score < 0.35:
                continue
            if not re.search(r"[A-Z0-9\u0600-\u06FF]{4,}", text):
                continue
            readings.append(PlateReading(text=text, confidence=score, box=(0, 0, 0, 0), crop=crop))
            if len(readings) >= 2:
                break
        deduped: dict[str, PlateReading] = {}
        for reading in readings:
            current = deduped.get(reading.text)
            if current is None or reading.confidence > current.confidence:
                deduped[reading.text] = reading
        return sorted(deduped.values(), key=lambda r: r.confidence, reverse=True)

    def scan_vehicle(self, image: np.ndarray, vehicle_box: tuple[int, int, int, int]) -> list[PlateReading]:
        x1, y1, x2, y2 = vehicle_box
        h, w = image.shape[:2]
        pad_x = int((x2 - x1) * 0.08)
        pad_y = int((y2 - y1) * 0.08)
        crop = image[max(0, y1 - pad_y) : min(h, y2 + pad_y), max(0, x1 - pad_x) : min(w, x2 + pad_x)]
        if crop.size == 0:
            return []
        readings = self.scan(crop, max_candidates=2)
        adjusted = []
        for reading in readings:
            adjusted.append(
                PlateReading(
                    text=reading.text,
                    confidence=reading.confidence,
                    box=vehicle_box,
                    crop=reading.crop,
                )
            )
        return adjusted


def lookup_vehicle(plate: str) -> dict:
    normalized = normalize_plate(plate)
    row = db.fetch_one("SELECT * FROM vehicles WHERE plate = ?", (normalized,))
    if row:
        return {
            "plate": normalized,
            "make": row.get("make", ""),
            "model": row.get("model", ""),
            "color": row.get("color", ""),
            "owner": row.get("owner", ""),
            "registered": True,
            "source": "local-registry",
        }
    if VEHICLE_LOOKUP_URL:
        try:
            response = requests.get(
                VEHICLE_LOOKUP_URL,
                params={"plate": normalized},
                timeout=8,
                headers={"User-Agent": "SentinelAICamera/1.0"},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "plate": normalized,
                "make": str(data.get("make", "")),
                "model": str(data.get("model", "")),
                "color": str(data.get("color", "")),
                "owner": str(data.get("owner", "")),
                "registered": bool(data.get("make") or data.get("model")),
                "source": "external-api",
            }
        except Exception as exc:  # noqa: BLE001
            log.debug("External vehicle lookup failed: %s", exc)
    return {
        "plate": normalized,
        "make": "",
        "model": "",
        "color": "",
        "owner": "",
        "registered": False,
        "source": "not-found",
    }

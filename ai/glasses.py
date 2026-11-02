from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from ai.face import FaceMatch


@dataclass
class EyewearResult:
    detected: bool
    kind: str = "none"
    confidence: float = 0.0
    note: str = ""

    def label(self) -> str:
        if not self.detected:
            return "No eyewear"
        return {
            "vision_glasses": "Vision glasses",
            "sunglasses": "Sunglasses",
            "possible_smart_glasses": "Possible smart glasses",
            "eyewear": "Eyewear (type uncertain)",
        }.get(self.kind, "Eyewear")


class GlassesAnalyzer:
    """Heuristic eyewear check.

    It can flag opaque lenses or possible camera-glasses reflections, but it cannot reliably
    prove that glasses contain a camera. Results are advisory and require human review.
    """

    def analyze(self, frame: np.ndarray, face: FaceMatch) -> EyewearResult:
        try:
            x1, y1, x2, y2 = face.box
            w, h = x2 - x1, y2 - y1
            if w < 28 or h < 28:
                return EyewearResult(False)
            eye_y = int(y1 + h * 0.45)
            band = frame[max(0, y1 + int(h * 0.22)) : min(frame.shape[0], eye_y), max(0, x1) : min(frame.shape[1], x2)]
            if band.size == 0 or band.shape[0] < 8 or band.shape[1] < 12:
                return EyewearResult(False, note="Eye region too small")
            gray = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
            if gray.size == 0:
                return EyewearResult(False)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            mean = float(gray.mean())
            std = float(gray.std())
            dark_ratio = float((gray < max(35, mean * 0.58)).mean())
            edges = cv2.Canny(gray, 55, 140)
            edge_ratio = float((edges > 0).mean())
            bright = float((gray > min(245, mean + 65)).mean())

            if dark_ratio > 0.30 and std < 55:
                return EyewearResult(
                    True,
                    "sunglasses",
                    min(0.95, 0.55 + dark_ratio),
                    "Dark lenses detected. Cannot determine if a camera is built in.",
                )
            if edge_ratio > 0.075 and std > 22:
                glare_ratio = float((gray > 238).mean())
                lens_like = self._lens_like_glare(gray)
                if lens_like and glare_ratio > 0.012:
                    return EyewearResult(
                        True,
                        "possible_smart_glasses",
                        min(0.72, 0.42 + glare_ratio * 4),
                        "Eyewear with small lens-like reflections. Possible camera glasses; verify manually.",
                    )
                if bright > 0.02:
                    return EyewearResult(
                        True,
                        "eyewear",
                        0.5,
                        "Reflective eyewear detected. Type cannot be confirmed from this view.",
                    )
                return EyewearResult(
                    True,
                    "vision_glasses",
                    min(0.82, 0.45 + edge_ratio),
                    "Frame/edge pattern is consistent with vision glasses.",
                )
            return EyewearResult(False)
        except Exception:  # noqa: BLE001
            return EyewearResult(False)

    @staticmethod
    def _lens_like_glare(gray: np.ndarray) -> bool:
        try:
            circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1.2,
                minDist=max(8, gray.shape[1] // 5),
                param1=80,
                param2=16,
                minRadius=2,
                maxRadius=max(5, gray.shape[1] // 10),
            )
            return circles is not None and len(circles[0]) >= 1
        except cv2.error:
            return False

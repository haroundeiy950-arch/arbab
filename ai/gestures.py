from __future__ import annotations

import json
import logging
import threading
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from config import DATA_DIR

log = logging.getLogger(__name__)

SIGNS_FILE = DATA_DIR / "signs.json"

DEFAULT_SIGNS: dict[str, dict[str, str]] = {
    "wave": {"en": "Greeting / hello", "ar": "تحية / مرحبا"},
    "raised_hand": {"en": "Asking for attention or help", "ar": "طلب الانتباه أو المساعدة"},
    "both_hands_raised": {"en": "Attention / please stop", "ar": "انتباه / توقف من فضلك"},
    "arms_out": {"en": "Open arms / welcome or attention", "ar": "أذرع مفتوحة / ترحيب أو انتباه"},
    "arm_extended": {"en": "Pointing or stop signal - verify visually", "ar": "إشارة توقف أو إشارة اتجاه - تحقق بصرياً"},
    "head_nod": {"en": "Yes / agreement", "ar": "نعم / موافقة"},
    "head_shake": {"en": "No / disagreement", "ar": "لا / رفض"},
    "phone_to_ear": {"en": "Talking on a phone", "ar": "يتحدث عبر الهاتف"},
}


@dataclass
class GestureResult:
    name: str
    meaning_en: str
    meaning_ar: str
    confidence: float

    def __bool__(self) -> bool:
        return bool(self.name)


def load_signs() -> dict[str, dict[str, str]]:
    if not SIGNS_FILE.exists():
        try:
            SIGNS_FILE.write_text(json.dumps(DEFAULT_SIGNS, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass
        return DEFAULT_SIGNS
    try:
        data = json.loads(SIGNS_FILE.read_text(encoding="utf-8"))
        signs = dict(DEFAULT_SIGNS)
        signs.update(data)
        return signs
    except (OSError, ValueError):
        return DEFAULT_SIGNS


class GestureInterpreter:
    """Rule-based interpretation of COCO-17 pose keypoints with short motion history."""

    def __init__(self) -> None:
        self._history: dict[int, deque] = {}
        self._lock = threading.RLock()
        self.signs = load_signs()

    def reload(self) -> None:
        with self._lock:
            self.signs = load_signs()

    @staticmethod
    def _pt(points: np.ndarray, idx: int, conf: np.ndarray | None = None) -> tuple[float, float] | None:
        if idx >= points.shape[0]:
            return None
        x, y = float(points[idx][0]), float(points[idx][1])
        if conf is not None and idx < conf.shape[0] and float(conf[idx]) < 0.25:
            return None
        if not np.isfinite(x) or not np.isfinite(y) or (x == 0 and y == 0):
            return None
        return x, y

    def _result(self, name: str, confidence: float) -> GestureResult:
        sign = self.signs.get(name, DEFAULT_SIGNS.get(name, {"en": name, "ar": name}))
        return GestureResult(name, sign.get("en", name), sign.get("ar", name), round(confidence, 2))

    def update(
        self,
        track_id: int,
        keypoints: np.ndarray,
        conf: np.ndarray | None,
        box: tuple[float, float, float, float],
    ) -> GestureResult | None:
        x1, y1, x2, y2 = box
        h = max(1.0, y2 - y1)
        w = max(1.0, x2 - x1)
        nose = self._pt(keypoints, 0, conf)
        l_sh = self._pt(keypoints, 5, conf)
        r_sh = self._pt(keypoints, 6, conf)
        l_wr = self._pt(keypoints, 9, conf)
        r_wr = self._pt(keypoints, 10, conf)
        if not (l_sh and r_sh) or not nose:
            return None
        shoulder_y = (l_sh[1] + r_sh[1]) / 2
        shoulder_w = max(20.0, abs(l_sh[0] - r_sh[0]))
        shoulder_mid_x = (l_sh[0] + r_sh[0]) / 2
        above_margin = 0.04 * h
        horiz_margin = 0.16 * h

        left_up = bool(l_wr and l_wr[1] < l_sh[1] - above_margin)
        right_up = bool(r_wr and r_wr[1] < r_sh[1] - above_margin)
        left_out = bool(
            l_wr
            and abs(l_wr[1] - l_sh[1]) < horiz_margin
            and abs(l_wr[0] - l_sh[0]) > shoulder_w * 0.75
        )
        right_out = bool(
            r_wr
            and abs(r_wr[1] - r_sh[1]) < horiz_margin
            and abs(r_wr[0] - r_sh[0]) > shoulder_w * 0.75
        )

        with self._lock:
            history = self._history.setdefault(track_id, deque(maxlen=14))
            history.append(
                {
                    "nose_x": nose[0],
                    "nose_y": nose[1],
                    "l_wr_x": l_wr[0] if l_wr else None,
                    "l_wr_y": l_wr[1] if l_wr else None,
                    "r_wr_x": r_wr[0] if r_wr else None,
                    "r_wr_y": r_wr[1] if r_wr else None,
                }
            )
            history_list = list(history)

        if len(history_list) >= 5:
            nose_xs = [item["nose_x"] for item in history_list[-7:]]
            nose_ys = [item["nose_y"] for item in history_list[-7:]]
            if self._oscillates(nose_xs, shoulder_w * 0.10):
                return self._result("head_shake", 0.62)
            if self._oscillates(nose_ys, shoulder_w * 0.08):
                return self._result("head_nod", 0.6)

        if (left_up or right_up) and len(history_list) >= 6:
            wrist_key = "l_wr_x" if left_up else "r_wr_x"
            xs = [item[wrist_key] for item in history_list[-8:] if item[wrist_key] is not None]
            if len(xs) >= 5 and self._oscillates(xs, max(14.0, shoulder_w * 0.28)):
                return self._result("wave", 0.78)

        if left_up and right_up:
            return self._result("both_hands_raised", 0.72)
        if left_up or right_up:
            wrist = l_wr if left_up else r_wr
            if wrist and abs(wrist[0] - nose[0]) < shoulder_w * 0.6:
                return self._result("phone_to_ear", 0.45)
            return self._result("raised_hand", 0.66)
        if left_out and right_out:
            return self._result("arms_out", 0.68)
        if left_out or right_out:
            return self._result("arm_extended", 0.5)
        return None

    @staticmethod
    def _oscillates(values: list[float], min_amplitude: float) -> bool:
        cleaned = [v for v in values if v is not None]
        if len(cleaned) < 4:
            return False
        amplitude = max(cleaned) - min(cleaned)
        if amplitude < min_amplitude:
            return False
        direction_changes = 0
        last_sign = 0
        for a, b in zip(cleaned, cleaned[1:]):
            delta = b - a
            if abs(delta) < 1.5:
                continue
            sign = 1 if delta > 0 else -1
            if last_sign and sign != last_sign:
                direction_changes += 1
            last_sign = sign
        return direction_changes >= 2

    def forget(self, active_ids: set[int]) -> None:
        with self._lock:
            for track_id in list(self._history):
                if track_id not in active_ids:
                    del self._history[track_id]

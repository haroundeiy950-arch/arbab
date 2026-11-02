from __future__ import annotations

import logging
import math
import time
from pathlib import Path

import cv2
import numpy as np

log = logging.getLogger(__name__)


class SyntheticSource:
    """Animated fallback source so the website remains usable without a camera."""

    demo = True

    def __init__(self, width: int = 960, height: int = 540) -> None:
        self.width = width
        self.height = height
        self._started = time.time()
        self._frame_index = 0

    def isOpened(self) -> bool:  # noqa: N802
        return True

    def read(self):
        self._frame_index += 1
        t = time.time() - self._started
        width, height = self.width, self.height
        x = np.linspace(0, 1, width, dtype=np.float32)
        y = np.linspace(0, 1, height, dtype=np.float32)[:, None]
        base = np.zeros((height, width, 3), dtype=np.uint8)
        base[:, :, 0] = (18 + 20 * y).astype(np.uint8)
        base[:, :, 1] = (24 + 22 * np.sin(x * 3 + t) + 10).astype(np.uint8)
        base[:, :, 2] = (32 + 18 * np.cos(y * 4 - t * 0.4)).astype(np.uint8)

        for i in range(3):
            phase = t * (0.55 + i * 0.16) + i * 2.1
            cx = int(width * (0.18 + 0.30 * i) + math.sin(phase) * width * 0.11)
            cy = int(height * 0.58 + math.cos(phase * 0.8) * height * 0.10)
            radius = int(height * (0.055 + i * 0.008))
            color = (100 + i * 40, 180 - i * 30, 90 + i * 50)
            cv2.circle(base, (cx, cy), radius, color, -1, cv2.LINE_AA)
            cv2.rectangle(
                base,
                (cx - radius, cy),
                (cx + radius, cy + radius * 4),
                (55 + i * 30, 62 + i * 25, 70 + i * 20),
                -1,
            )
        overlay = base.copy()
        cv2.rectangle(overlay, (0, 0), (width, 85), (10, 15, 24), -1)
        base = cv2.addWeighted(overlay, 0.55, base, 0.45, 0)
        cv2.putText(
            base,
            "DEMO FEED - NO CAMERA DETECTED",
            (24, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (80, 230, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            base,
            "Connect a USB camera or set a video source in Settings",
            (24, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (190, 200, 215),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            base,
            time.strftime("%Y-%m-%d %H:%M:%S"),
            (width - 235, height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (200, 210, 225),
            1,
            cv2.LINE_AA,
        )
        return True, base

    def release(self) -> None:
        return None

    def set(self, *args, **kwargs) -> None:  # noqa: N802
        return None


class VideoSource:
    def __init__(self, source: str, width: int = 960, height: int = 540) -> None:
        self.source = source
        self.width = width
        self.height = height
        self.demo = False
        self._cap = None
        self._is_file = False
        self._open()

    def _open(self) -> None:
        source = (self.source or "0").strip()
        if source.isdigit() or source.startswith("http") or source.startswith("rtsp"):
            target: int | str = int(source) if source.isdigit() else source
            backend = cv2.CAP_DSHOW if source.isdigit() else cv2.CAP_ANY
            cap = cv2.VideoCapture(target, backend)
        else:
            path = Path(source).expanduser()
            if not path.is_absolute():
                path = Path.cwd() / path
            self._is_file = True
            cap = cv2.VideoCapture(str(path))
        if cap is None or not cap.isOpened():
            log.warning("Camera source %s could not be opened; using demo feed", source)
            self._cap = SyntheticSource(self.width, self.height)
            self.demo = True
            return
        if not self._is_file:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        ok, frame = cap.read()
        if not ok or frame is None:
            log.warning("Camera source %s opened but produced no frames; using demo feed", source)
            cap.release()
            self._cap = SyntheticSource(self.width, self.height)
            self.demo = True
            return
        self._cap = cap
        self._first_frame = frame

    def read(self):
        if self._cap is None:
            return False, None
        ok, frame = self._cap.read()
        if not ok and self._is_file and not self.demo:
            try:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._cap.read()
            except Exception:  # noqa: BLE001
                ok = False
        if not ok and not self.demo:
            log.warning("Camera stopped returning frames; switching to demo feed")
            self.release()
            self._cap = SyntheticSource(self.width, self.height)
            self.demo = True
            return self._cap.read()
        return ok, frame

    def release(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:  # noqa: BLE001
                pass
            self._cap = None

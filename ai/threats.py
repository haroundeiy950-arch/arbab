from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from config import WEAPON_MODEL
from core import database as db

if TYPE_CHECKING:
    from ai.detector import Detection

log = logging.getLogger(__name__)

CRITICAL_LABELS = {
    "knife",
    "gun",
    "guns",
    "pistol",
    "rifle",
    "firearm",
    "weapon",
    "grenade",
    "explosive",
    "sword",
    "machete",
    "axe",
}

WARNING_LABELS = {"scissors", "baseball bat", "baton", "hammer", "crowbar", "screwdriver"}


@dataclass
class ThreatFinding:
    label: str
    confidence: float
    box: tuple[int, int, int, int]
    severity: str
    person_box: tuple[int, int, int, int] | None = None

    def display_label(self) -> str:
        return self.label.replace("_", " ").title()


class ThreatScanner:
    """Visible restricted-item detection. Never infers concealed objects or body contents."""

    def __init__(self) -> None:
        self._custom_model = None
        self.custom_available = False
        if WEAPON_MODEL.exists():
            try:
                from ultralytics import YOLO

                self._custom_model = YOLO(str(WEAPON_MODEL))
                self.custom_available = True
                log.info("Custom restricted-item model loaded")
            except Exception as exc:  # noqa: BLE001
                log.warning("Custom weapon model could not be loaded: %s", exc)

    @property
    def restricted_labels(self) -> set[str]:
        raw = db.get_setting("restricted_classes", "knife,scissors,baseball bat")
        return {item.strip().lower() for item in raw.split(",") if item.strip()}

    @property
    def enabled(self) -> bool:
        return db.get_bool_setting("threat_detection", True)

    @staticmethod
    def _center(box: tuple[int, int, int, int]) -> tuple[float, float]:
        return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)

    def _assign_person(self, box: tuple[int, int, int, int], persons: list) -> tuple[int, int, int, int] | None:
        if not persons:
            return None
        cx, cy = self._center(box)
        best = None
        best_distance = 1e12
        for person in persons:
            px1, py1, px2, py2 = person.box
            pad_x, pad_y = (px2 - px1) * 0.35, (py2 - py1) * 0.2
            if px1 - pad_x <= cx <= px2 + pad_x and py1 - pad_y <= cy <= py2 + pad_y:
                return person.box
            pcx, pcy = self._center(person.box)
            distance = (pcx - cx) ** 2 + (pcy - cy) ** 2
            if distance < best_distance:
                best_distance = distance
                best = person.box
        area = max(1, (box[2] - box[0]) * (box[3] - box[1]))
        if best and best_distance < area * 4:
            return best
        return None

    def scan(self, detections: list["Detection"], persons: list["Detection"]) -> list[ThreatFinding]:
        if not self.enabled:
            return []
        restricted = self.restricted_labels
        findings: list[ThreatFinding] = []
        seen: set[tuple[str, int, int]] = set()
        for det in detections:
            label = det.label.lower()
            if label not in restricted and label not in CRITICAL_LABELS:
                continue
            if det.confidence < 0.4:
                continue
            person_box = self._assign_person(det.box, persons)
            severity = "critical" if label in CRITICAL_LABELS else "warning"
            key = (label, det.box[0] // 60, det.box[1] // 60)
            if key in seen:
                continue
            seen.add(key)
            findings.append(ThreatFinding(label, det.confidence, det.box, severity, person_box))
        findings.sort(key=lambda f: (f.severity == "critical", f.confidence), reverse=True)
        return findings

    def scan_custom(self, frame: np.ndarray) -> list["Detection"]:
        if self._custom_model is None:
            return []
        from ai.detector import Detection

        try:
            result = self._custom_model.predict(frame, conf=0.4, verbose=False)[0]
        except Exception as exc:  # noqa: BLE001
            log.debug("Custom threat model failed: %s", exc)
            return []
        detections: list[Detection] = []
        if result.boxes is None:
            return detections
        names = result.names or {}
        for box in result.boxes:
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            cls = int(box.cls[0].item()) if box.cls is not None else -1
            conf = float(box.conf[0].item()) if box.conf is not None else 0.0
            detections.append(
                Detection(
                    label=str(names.get(cls, str(cls))).lower(),
                    confidence=conf,
                    box=(x1, y1, x2, y2),
                    class_id=cls,
                )
            )
        return detections

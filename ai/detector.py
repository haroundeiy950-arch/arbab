from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field

import numpy as np

from config import POSE_MODEL, YOLO_MODEL
from core import database as db

log = logging.getLogger(__name__)


@dataclass
class Detection:
    label: str
    confidence: float
    box: tuple[int, int, int, int]
    class_id: int = -1
    track_id: int | None = None


@dataclass
class PoseDetection:
    box: tuple[int, int, int, int]
    confidence: float
    keypoints: np.ndarray
    keypoint_conf: np.ndarray | None
    track_id: int | None = None


@dataclass
class FrameAnalysis:
    detections: list[Detection] = field(default_factory=list)
    persons: list[Detection] = field(default_factory=list)
    vehicles: list[Detection] = field(default_factory=list)
    phones: list[Detection] = field(default_factory=list)
    poses: list[PoseDetection] = field(default_factory=list)
    person_count: int = 0
    unique_person_ids: set[int] = field(default_factory=set)


class ObjectDetector:
    TRACK_CLASS_NAMES = {
        "person",
        "bicycle",
        "car",
        "motorcycle",
        "bus",
        "truck",
        "cell phone",
        "knife",
        "scissors",
        "baseball bat",
        "bottle",
    }

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._model = None
        self._pose_model = None
        self._track_ready = False
        self._pose_track_ready = False
        self._class_ids: list[int] = []
        self._last_track_ids: set[int] = set()
        self.available = False
        self.pose_available = False
        if YOLO_MODEL.exists():
            try:
                from ultralytics import YOLO

                self._model = YOLO(str(YOLO_MODEL))
                names = self._model.names or {}
                self._class_ids = [
                    int(cid)
                    for cid, name in names.items()
                    if str(name).lower() in self.TRACK_CLASS_NAMES
                ]
                self.available = True
                log.info("Detector loaded with %d target classes", len(self._class_ids))
            except Exception as exc:  # noqa: BLE001
                log.error("Could not load YOLO detector: %s", exc)
        else:
            log.warning("YOLO model missing at %s", YOLO_MODEL)
        if POSE_MODEL.exists():
            try:
                from ultralytics import YOLO

                self._pose_model = YOLO(str(POSE_MODEL))
                self.pose_available = True
                log.info("Pose model loaded")
            except Exception as exc:  # noqa: BLE001
                log.error("Could not load pose model: %s", exc)

    def detect(self, frame: np.ndarray, tracking: bool = True) -> list[Detection]:
        if self._model is None:
            return []
        conf = db.get_float_setting("person_confidence", 0.35)
        detections: list[Detection] = []
        with self._lock:
            try:
                if tracking:
                    results = self._model.track(
                        frame,
                        persist=True,
                        conf=conf,
                        iou=0.45,
                        classes=self._class_ids or None,
                        verbose=False,
                        tracker="bytetrack.yaml",
                        imgsz=640,
                    )
                    self._track_ready = True
                else:
                    results = self._model.predict(
                        frame, conf=conf, iou=0.45, classes=self._class_ids or None, verbose=False, imgsz=640
                    )
            except Exception as exc:  # noqa: BLE001
                log.warning("Tracking failed, falling back to detection: %s", exc)
                try:
                    results = self._model.predict(
                        frame, conf=conf, iou=0.45, classes=self._class_ids or None, verbose=False, imgsz=640
                    )
                except Exception as exc2:  # noqa: BLE001
                    log.error("Object detection failed: %s", exc2)
                    return []
        for result in results:
            if result.boxes is None:
                continue
            names = result.names or {}
            ids = result.boxes.id
            for index, box in enumerate(result.boxes):
                x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
                class_id = int(box.cls[0].item()) if box.cls is not None else -1
                confidence = float(box.conf[0].item()) if box.conf is not None else 0.0
                track_id = int(ids[index].item()) if ids is not None and index < len(ids) else None
                detections.append(
                    Detection(
                        label=str(names.get(class_id, str(class_id))),
                        confidence=confidence,
                        box=(x1, y1, x2, y2),
                        class_id=class_id,
                        track_id=track_id,
                    )
                )
        return detections

    def detect_pose(self, frame: np.ndarray, tracking: bool = True) -> list[PoseDetection]:
        if self._pose_model is None:
            return []
        poses: list[PoseDetection] = []
        with self._lock:
            try:
                if tracking:
                    results = self._pose_model.track(
                        frame,
                        persist=True,
                        conf=0.4,
                        iou=0.45,
                        verbose=False,
                        tracker="bytetrack.yaml",
                        imgsz=640,
                        classes=[0],
                    )
                    self._pose_track_ready = True
                else:
                    results = self._pose_model.predict(
                        frame, conf=0.4, iou=0.45, verbose=False, imgsz=640, classes=[0]
                    )
            except Exception as exc:  # noqa: BLE001
                log.debug("Pose tracking failed, falling back: %s", exc)
                try:
                    results = self._pose_model.predict(
                        frame, conf=0.4, iou=0.45, verbose=False, imgsz=640, classes=[0]
                    )
                except Exception as exc2:  # noqa: BLE001
                    log.debug("Pose detection failed: %s", exc2)
                    return []
        for result in results:
            if result.boxes is None or result.keypoints is None:
                continue
            ids = result.boxes.id
            boxes = result.boxes.xyxy.tolist()
            keypoints_xy = result.keypoints.xy
            keypoints_conf = result.keypoints.conf
            for index, coords in enumerate(boxes):
                if index >= len(keypoints_xy):
                    continue
                x1, y1, x2, y2 = (int(v) for v in coords)
                confidence = float(result.boxes.conf[index].item()) if result.boxes.conf is not None else 0.0
                track_id = int(ids[index].item()) if ids is not None and index < len(ids) else None
                poses.append(
                    PoseDetection(
                        box=(x1, y1, x2, y2),
                        confidence=confidence,
                        keypoints=np.asarray(keypoints_xy[index].cpu(), dtype=np.float32),
                        keypoint_conf=(
                            np.asarray(keypoints_conf[index].cpu(), dtype=np.float32)
                            if keypoints_conf is not None
                            else None
                        ),
                        track_id=track_id,
                    )
                )
        return poses

    def analyze(self, frame: np.ndarray, run_pose: bool = True) -> FrameAnalysis:
        detections = self.detect(frame, tracking=True)
        persons = [d for d in detections if d.label == "person"]
        vehicles = [d for d in detections if d.label in {"car", "truck", "bus", "motorcycle", "bicycle"}]
        phones = [d for d in detections if d.label == "cell phone"]
        tracked_ids = {d.track_id for d in persons if d.track_id is not None and d.track_id > 0}
        self._last_track_ids.update(tracked_ids)
        poses = self.detect_pose(frame, tracking=True) if run_pose else []
        return FrameAnalysis(
            detections=detections,
            persons=persons,
            vehicles=vehicles,
            phones=phones,
            poses=poses,
            person_count=len(persons),
            unique_person_ids=tracked_ids,
        )

    @property
    def unique_people_seen(self) -> int:
        return len(self._last_track_ids)

    def reset_session(self) -> None:
        self._last_track_ids.clear()

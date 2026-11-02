from __future__ import annotations

import logging
import re
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

import cv2
import numpy as np

from ai.detector import Detection, FrameAnalysis, ObjectDetector
from ai.face import FaceEngine, FaceMatch
from ai.gestures import GestureInterpreter, GestureResult
from ai.glasses import GlassesAnalyzer, EyewearResult
from ai.plates import PlateEngine, format_plate, lookup_vehicle
from ai.threats import ThreatFinding, ThreatScanner
from ai.translate import TranslationService
from core import database as db
from core.events import EventManager
from core.storage import clip_path, relative_path, save_jpeg
from services.video_source import VideoSource

log = logging.getLogger(__name__)

_COCO_SKELETON = [
    (5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12),
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (0, 1), (0, 2),
    (1, 3), (2, 4),
]
_COLORS = {
    "known": (80, 220, 120),
    "unknown": (0, 170, 255),
    "person": (170, 200, 230),
    "threat": (40, 40, 255),
    "vehicle": (255, 160, 40),
    "phone": (0, 210, 255),
    "gesture": (230, 220, 50),
    "pose": (190, 150, 255),
}


def _ascii(text: str) -> str:
    cleaned = text.encode("ascii", "ignore").decode("ascii").strip()
    return cleaned or "ID"


def _center(box: tuple[int, int, int, int]) -> tuple[float, float]:
    return (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0


def _inside(point: tuple[float, float], box: tuple[int, int, int, int], pad: float = 0.0) -> bool:
    x, y = point
    x1, y1, x2, y2 = box
    return x1 - pad <= x <= x2 + pad and y1 - pad <= y <= y2 + pad


def _distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax, ay = _center(a)
    bx, by = _center(b)
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


class CameraService:
    def __init__(
        self,
        face_engine: FaceEngine,
        translator: TranslationService,
        events: EventManager,
    ) -> None:
        self.face_engine = face_engine
        self.translator = translator
        self.events = events
        self.detector = ObjectDetector()
        self.glasses = GlassesAnalyzer()
        self.gestures = GestureInterpreter()
        self.plates = PlateEngine()
        self.threats = ThreatScanner()

        self._cfg: dict[str, str] = {}
        self._refresh_config()

        self._frame_lock = threading.RLock()
        self._state_lock = threading.RLock()
        self._record_lock = threading.RLock()
        self._running = False
        self._capture_thread: threading.Thread | None = None
        self._ai_thread: threading.Thread | None = None
        self._clip_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="clip")
        self._plate_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="plate")

        self._source_string = self._cfg.get("camera_source", "0")
        self._pending_source: str | None = None
        self._source: VideoSource | None = None
        self._demo = False
        self._width = int(self._cfg.get("frame_width", 960))
        self._height = int(self._cfg.get("frame_height", 540))

        self._latest_raw: np.ndarray | None = None
        self._latest_annotated: np.ndarray | None = None
        self._latest_jpeg: bytes | None = None
        self._frame_counter = 0
        self._analyzed_counter = -1
        self._analysis: FrameAnalysis | None = None
        self._faces: list[FaceMatch] = []
        self._eyewear: dict[int, EyewearResult] = {}
        self._gesture_display: dict[int, tuple[GestureResult, float, tuple[int, int, int, int]]] = {}
        self._alarm: dict[str, Any] | None = None
        self._plate_overlay: dict[str, Any] | None = None
        self._last_event: dict[str, Any] | None = None
        self._motion_boxes: list[tuple[int, int, int, int]] = []
        self._motion_boxes_until = 0.0
        self._prev_small: np.ndarray | None = None
        self._ring: deque[np.ndarray] = deque(maxlen=55)

        self._people_count = 0
        self._known_count = 0
        self._unknown_count = 0
        self._unique_seen = 0
        self._avg_fps = 0.0
        self._timestamps: deque[float] = deque(maxlen=40)
        self._started_at = time.time()
        self._last_analysis_time = 0.0
        self._last_plate_time = 0.0
        self._last_motion_time = 0.0
        self._tick = 0

        self._recording = False
        self._writer: cv2.VideoWriter | None = None
        self._recording_rel = ""

    def _refresh_config(self) -> None:
        try:
            self._cfg = db.all_settings()
        except Exception:  # noqa: BLE001
            log.debug("Could not load runtime settings", exc_info=True)

    def _cfg_bool(self, key: str, default: bool = True) -> bool:
        value = self._cfg.get(key, "1" if default else "0").strip().lower()
        return value in {"1", "true", "yes", "on"}

    def _cfg_float(self, key: str, default: float) -> float:
        try:
            return float(self._cfg.get(key, default))
        except (TypeError, ValueError):
            return default

    def _cfg_int(self, key: str, default: int) -> int:
        try:
            return int(float(self._cfg.get(key, default)))
        except (TypeError, ValueError):
            return default

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._source = VideoSource(self._source_string, self._width, self._height)
        self._demo = getattr(self._source, "demo", False)
        self._capture_thread = threading.Thread(target=self._capture_loop, name="camera-capture", daemon=True)
        self._ai_thread = threading.Thread(target=self._ai_loop, name="camera-ai", daemon=True)
        self._capture_thread.start()
        self._ai_thread.start()
        log.info("Camera service started (demo=%s)", self._demo)

    def stop(self) -> None:
        self._running = False
        self._stop_recording(silent=True)
        for thread in (self._capture_thread, self._ai_thread):
            if thread and thread.is_alive():
                thread.join(timeout=4)
        if self._source:
            self._source.release()
        self._clip_executor.shutdown(wait=False, cancel_futures=True)
        self._plate_executor.shutdown(wait=False, cancel_futures=True)
        log.info("Camera service stopped")

    def switch_source(self, source: str) -> None:
        with self._state_lock:
            self._pending_source = (source or "0").strip()
        db.log_audit("camera_source_change", self._pending_source, actor="admin")

    def _capture_loop(self) -> None:
        target_dt = 1.0 / 20.0
        last_settings = 0.0
        while self._running:
            started = time.time()
            if time.time() - last_settings > 2.0:
                self._refresh_config()
                last_settings = time.time()
                pending = self._pending_source
                if pending is not None:
                    self._pending_source = None
                    self._source_string = pending
                    self._width = self._cfg_int("frame_width", 960)
                    self._height = self._cfg_int("frame_height", 540)
                    if self._source:
                        self._source.release()
                    self._source = VideoSource(pending, self._width, self._height)
                    self._demo = getattr(self._source, "demo", False)
                    self.detector.reset_session()
                    self._unique_seen = 0
                    log.info("Camera source switched to %s (demo=%s)", pending, self._demo)

            if self._source is None:
                time.sleep(0.1)
                continue
            ok, frame = self._source.read()
            if not ok or frame is None:
                time.sleep(0.05)
                continue

            target_w = self._cfg_int("frame_width", self._width)
            target_h = self._cfg_int("frame_height", self._height)
            if target_w != self._width or target_h != self._height:
                self._width, self._height = target_w, target_h
            if frame.shape[1] != target_w or frame.shape[0] != target_h:
                frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)

            with self._frame_lock:
                self._latest_raw = frame
                self._frame_counter += 1
                frame_id = self._frame_counter
                annotated = self._annotate(frame)
                self._latest_annotated = annotated
                ok_enc, buffer = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
                if ok_enc:
                    self._latest_jpeg = buffer.tobytes()
            if frame_id % 2 == 0:
                self._ring.append(annotated)
            with self._record_lock:
                if self._recording and self._writer is not None:
                    self._writer.write(annotated)

            self._timestamps.append(time.time())
            if len(self._timestamps) > 3:
                span = self._timestamps[-1] - self._timestamps[0]
                self._avg_fps = (len(self._timestamps) - 1) / span if span > 0 else 0.0
            elapsed = time.time() - started
            if elapsed < target_dt:
                time.sleep(target_dt - elapsed)

    def _ai_loop(self) -> None:
        while self._running:
            try:
                if not self._cfg_bool("ai_enabled", True):
                    time.sleep(0.4)
                    continue
                interval = max(0.15, self._cfg_float("detection_interval", 0.35))
                now = time.time()
                with self._frame_lock:
                    frame = None if self._latest_raw is None else self._latest_raw.copy()
                    frame_id = self._frame_counter
                if frame is None or frame_id == self._analyzed_counter or now - self._last_analysis_time < interval:
                    time.sleep(0.04)
                    continue
                self._last_analysis_time = now
                self._analyzed_counter = frame_id
                self._tick += 1
                self._analyze_frame(frame)
            except Exception:  # noqa: BLE001
                log.exception("AI analysis loop error")
                time.sleep(0.5)

    # ---------------------------------------------------------------- analysis

    def _analyze_frame(self, frame: np.ndarray) -> None:
        run_pose = self._cfg_bool("gesture_recognition", True) and self.detector.pose_available and self._tick % 2 == 0
        analysis = self.detector.analyze(frame, run_pose=run_pose)
        faces: list[FaceMatch] = []
        eyewear: dict[int, EyewearResult] = {}
        if self._cfg_bool("face_recognition", True):
            try:
                faces = self.face_engine.identify(frame, self.face_engine.detect(frame))
            except Exception as exc:  # noqa: BLE001
                log.debug("Face recognition failed: %s", exc)
            if self._cfg_bool("glasses_detection", True):
                for idx, face in enumerate(faces[:4]):
                    try:
                        eyewear[idx] = self.glasses.analyze(frame, face)
                    except Exception:  # noqa: BLE001
                        pass

        persons = analysis.persons
        known = sum(1 for face in faces if face.known)
        unknown = sum(1 for face in faces if not face.known)
        self._people_count = analysis.person_count
        self._known_count = known
        self._unknown_count = unknown
        self._unique_seen = max(self._unique_seen, self.detector.unique_people_seen)

        gesture_map: dict[int, tuple[GestureResult, float, tuple[int, int, int, int]]] = {}
        if run_pose and analysis.poses and self._cfg_bool("gesture_recognition", True):
            active_ids = set()
            for idx, pose in enumerate(analysis.poses[:6]):
                track_id = pose.track_id if pose.track_id is not None else 100000 + idx
                active_ids.add(track_id)
                gesture = self.gestures.update(track_id, pose.keypoints, pose.keypoint_conf, pose.box)
                if not gesture:
                    continue
                gesture_map[track_id] = (gesture, time.time() + 4.0, pose.box)
                person = self._person_for_box(pose.box, faces)
                if person and self.events.allow(f"gesture:{gesture.name}:{person['id']}", 20):
                    self._event(
                        "gesture",
                        "info",
                        f"Gesture interpreted: {gesture.name.replace('_', ' ').title()}",
                        f"Meaning: {gesture.meaning_en}.",
                        f"المعنى: {gesture.meaning_ar}.",
                        person=person,
                        frame=frame,
                        meta={"gesture": gesture.name, "meaning_en": gesture.meaning_en, "meaning_ar": gesture.meaning_ar},
                    )
                elif not person and self.events.allow(f"gesture:{gesture.name}:anon", 25):
                    self._event(
                        "gesture",
                        "info",
                        f"Gesture interpreted: {gesture.name.replace('_', ' ').title()}",
                        f"Meaning: {gesture.meaning_en}.",
                        f"المعنى: {gesture.meaning_ar}.",
                        frame=frame,
                        meta={"gesture": gesture.name, "meaning_en": gesture.meaning_en, "meaning_ar": gesture.meaning_ar},
                    )
            self.gestures.forget(active_ids)

        with self._state_lock:
            self._analysis = analysis
            self._faces = faces
            self._eyewear = eyewear
            for track_id, value in gesture_map.items():
                self._gesture_display[track_id] = value
            cutoff = time.time()
            self._gesture_display = {
                key: value for key, value in self._gesture_display.items() if value[1] > cutoff
            }

        self._handle_faces(frame, faces, eyewear, persons)
        self._handle_people_count(frame, analysis)
        self._handle_threats(frame, analysis, faces, persons)
        self._handle_phone(frame, analysis, faces, persons)
        self._handle_motion(frame)
        self._maybe_plate_scan(frame, analysis.vehicles)

    # ---------------------------------------------------------------- policies

    def _person_for_box(self, box: tuple[int, int, int, int], faces: list[FaceMatch]) -> dict | None:
        best_face = None
        best_distance = 1e12
        for face in faces:
            if not face.known or face.person is None:
                continue
            center = _center(face.box)
            if _inside(center, box, pad=30):
                distance = _distance(face.box, box)
                if distance < best_distance:
                    best_distance = distance
                    best_face = face
        return best_face.person if best_face else None

    def _handle_faces(
        self,
        frame: np.ndarray,
        faces: list[FaceMatch],
        eyewear: dict[int, EyewearResult],
        persons: list[Detection],
    ) -> None:
        for idx, face in enumerate(faces[:4]):
            if face.known and face.person:
                person = face.person
                if self.events.allow(f"known:{person['id']}", 150):
                    self._event(
                        "face_known",
                        "success",
                        f"Registered person recognized: {person['name']}",
                        f"{person['name']} was recognized with {face.similarity:.0%} similarity. "
                        f"Role: {person.get('role') or 'not specified'}.",
                        f"تم التعرف على {person['name']} بنسبة تشابه {face.similarity:.0%}.",
                        person=person,
                        frame=frame,
                        meta={"similarity": round(face.similarity, 4)},
                    )
                glasses = eyewear.get(idx)
                if (
                    glasses
                    and glasses.kind == "possible_smart_glasses"
                    and self._cfg_bool("smart_glasses_alerts", False)
                    and self.events.allow(f"smartglasses:{person['id']}", 300)
                ):
                    self._event(
                        "glasses",
                        "warning",
                        f"Possible smart glasses detected: {person['name']}",
                        f"{person['name']} appears to be wearing glasses with camera-like reflections. "
                        "The system cannot confirm this. Verify manually and follow the site policy.",
                        f"يبدو أن {person['name']} يرتدي نظارة بها انعكاسات تشبه الكاميرا. "
                        "لا يمكن للنظام تأكيد ذلك. تحقق يدوياً واتبع سياسة الموقع.",
                        person=person,
                        frame=frame,
                        meta={"eyewear": glasses.kind, "confidence": round(glasses.confidence, 3), "advisory": True},
                    )
            elif not face.known:
                if self._cfg_bool("alert_unknown_person", True) and self.events.allow("unknown_face", 75):
                    self._event(
                        "face_unknown",
                        "warning",
                        "Unknown person detected",
                        "A face not present in the consent-based registry is in view. "
                        "Review the snapshot and follow your visitor policy.",
                        "تم رصد وجه غير مسجل في قاعدة البيانات. راجع الصورة واتبع سياسة الزوار.",
                        frame=frame,
                        meta={"face_confidence": round(face.score, 3), "unknown_faces": sum(1 for f in faces if not f.known)},
                    )

    def _handle_people_count(self, frame: np.ndarray, analysis: FrameAnalysis) -> None:
        if not self._cfg_bool("count_persons", True):
            return
        if analysis.person_count >= 3 and self.events.allow("crowd", 60):
            self._event(
                "crowd",
                "info",
                f"Crowd detected: {analysis.person_count} people",
                f"{analysis.person_count} people are currently in view. "
                "The live count and registered matches are shown on the video overlay.",
                f"يوجد حالياً {analysis.person_count} أشخاص في المشهد. يتم عرض العدد الحالي والمطابقات على الفيديو.",
                frame=frame,
                meta={"count": analysis.person_count, "unique_seen": self._unique_seen},
            )

    def _handle_threats(
        self,
        frame: np.ndarray,
        analysis: FrameAnalysis,
        faces: list[FaceMatch],
        persons: list[Detection],
    ) -> None:
        if not self._cfg_bool("threat_detection", True):
            return
        detections = list(analysis.detections)
        if self._tick % 3 == 0 and self.threats.custom_available:
            detections.extend(self.threats.scan_custom(frame))
        findings = self.threats.scan(detections, persons)
        for finding in findings[:3]:
            person = self._person_for_box(finding.person_box, faces) if finding.person_box else None
            if self.events.allow(f"threat:{finding.label}", 18):
                self._handle_threat(frame, finding, person)

    def _handle_threat(self, frame: np.ndarray, finding: ThreatFinding, person: dict | None) -> None:
        name = person["name"] if person else ""
        item = finding.display_label()
        if name:
            title = f"Security alert: {name} may be carrying a {item.lower()}"
            description = (
                f"AI detected a possible {item.lower()} near {name} with {finding.confidence:.0%} confidence. "
                "This is a visual detection, not proof. Keep a safe distance, do not confront the person, "
                "and let trained security staff verify the situation. The alert has been logged."
            )
            description_ar = (
                f"اكتشف الذكاء الاصطناعي احتمال وجود {item} بالقرب من {name} بثقة {finding.confidence:.0%}. "
                "هذا اكتشاف بصري وليس دليلاً قاطعاً. ابق على مسافة آمنة ولا تواجه الشخص، "
                "ودع أفراد الأمن المدربين يتحققون من الموقف."
            )
            alarm_en = (
                f"Security alert. {name} appears to have a {item}. Stay away from this person. "
                "Security has been notified."
            )
            alarm_ar = f"تنبيه أمني. يبدو أن {name} يحمل {item}. ابتعد عن هذا الشخص. تم إبلاغ الأمن."
        else:
            title = f"Security alert: possible {item.lower()} detected"
            description = (
                f"AI detected a possible {item.lower()} near an unknown person with {finding.confidence:.0%} confidence. "
                "This is a visual detection, not proof. Keep a safe distance and let trained security staff verify."
            )
            description_ar = (
                f"اكتشف الذكاء الاصطناعي احتمال وجود {item} بالقرب من شخص غير معروف "
                f"بثقة {finding.confidence:.0%}. هذا اكتشاف بصري وليس دليلاً قاطعاً. ابق على مسافة آمنة."
            )
            alarm_en = (
                f"Security alert. An unknown person appears to have a {item}. Stay away. Security has been notified."
            )
            alarm_ar = f"تنبيه أمني. يبدو أن شخصاً غير معروف يحمل {item}. ابتعد. تم إبلاغ الأمن."
        severity = finding.severity
        alarm_active = self._cfg_bool("alarm_enabled", True) and severity == "critical"
        if alarm_active:
            with self._state_lock:
                self._alarm = {
                    "en": alarm_en,
                    "ar": alarm_ar,
                    "until": time.time() + 14,
                    "item": item,
                    "person": name,
                    "severity": severity,
                }
        event = self._event(
            "threat",
            severity,
            title,
            description,
            description_ar,
            person=person,
            frame=frame,
            meta={
                "item": finding.label,
                "confidence": round(finding.confidence, 3),
                "alarm_en": alarm_en,
                "alarm_ar": alarm_ar,
                "sound_alarm": alarm_active,
                "advisory": "Visual detection only. Human verification required.",
            },
            with_clip=True,
        )
        if event and severity == "critical" and self._cfg_bool("alarm_enabled", True):
            log.warning("CRITICAL ALERT: %s", alarm_en)

    def _handle_phone(
        self,
        frame: np.ndarray,
        analysis: FrameAnalysis,
        faces: list[FaceMatch],
        persons: list[Detection],
    ) -> None:
        if not analysis.phones:
            return
        if not self.events.allow("phone_use", 80):
            return
        person = None
        best = None
        best_distance = 1e12
        for phone in analysis.phones:
            for index, person_det in enumerate(persons):
                distance = _distance(phone.box, person_det.box)
                if distance < best_distance:
                    best_distance = distance
                    best = index
        if best is not None:
            person = self._person_for_box(persons[best].box, faces)
        self._event(
            "phone",
            "info",
            "Phone use detected",
            (
                "A person appears to be using a phone."
                + (f" Recognized person: {person['name']}." if person else "")
                + " If audio monitoring is enabled, nearby speech may be transcribed and translated."
            ),
            "يبدو أن شخصاً يستخدم الهاتف. إذا كان مراقبة الصوت مفعلة، فقد يتم نسخ الكلام القريب وترجمته.",
            person=person,
            frame=frame,
            meta={"phone_count": len(analysis.phones)},
        )

    def _handle_motion(self, frame: np.ndarray) -> None:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (160, 90), interpolation=cv2.INTER_AREA)
        with self._state_lock:
            previous = self._prev_small
            self._prev_small = small
        if previous is None:
            return
        diff = cv2.absdiff(small, previous)
        brightness_delta = abs(float(small.mean()) - float(previous.mean()))
        _, mask = cv2.threshold(diff, 24, 255, cv2.THRESH_BINARY)
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=2)
        ratio = float(np.count_nonzero(mask)) / mask.size
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        scale_x = frame.shape[1] / 160.0
        scale_y = frame.shape[0] / 90.0
        for contour in contours:
            if cv2.contourArea(contour) < 45:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            boxes.append((int(x * scale_x), int(y * scale_y), int((x + w) * scale_x), int((y + h) * scale_y)))
        boxes = boxes[:6]
        with self._state_lock:
            self._motion_boxes = boxes
            self._motion_boxes_until = time.time() + 1.2
        threshold = self._cfg_float("motion_threshold", 0.025)
        if (
            ratio >= threshold
            and brightness_delta < 24
            and boxes
            and self._cfg_bool("auto_save_motion", True)
            and self.events.allow("motion", 16)
        ):
            self._event(
                "motion",
                "info",
                "Meaningful movement detected",
                f"Motion was detected in {len(boxes)} region(s), covering {ratio * 100:.1f}% of the view. "
                "A snapshot was saved. Use the gesture panel for interpreted gestures.",
                f"تم اكتشاف حركة في {len(boxes)} منطقة، بنسبة {ratio * 100:.1f}% من المشهد. تم حفظ لقطة.",
                frame=frame,
                meta={"ratio": round(ratio, 4), "regions": len(boxes)},
            )

    def _maybe_plate_scan(self, frame: np.ndarray, vehicles: list[Detection]) -> None:
        if not self._cfg_bool("plate_recognition", True) or not vehicles:
            return
        now = time.time()
        if now - self._last_plate_time < 6:
            return
        self._last_plate_time = now
        frame_copy = frame.copy()
        try:
            self._plate_executor.submit(self._plate_scan, frame_copy, list(vehicles[:2]))
        except RuntimeError:
            pass

    def _plate_scan(self, frame: np.ndarray, vehicles: list[Detection]) -> None:
        readings = []
        try:
            for vehicle in vehicles:
                readings.extend(self.plates.scan_vehicle(frame, vehicle.box))
            if not readings:
                return
            readings.sort(key=lambda r: r.confidence, reverse=True)
            reading = readings[0]
            lookup = lookup_vehicle(reading.text)
            shown = format_plate(reading.text)
            with self._state_lock:
                self._plate_overlay = {
                    "text": shown,
                    "until": time.time() + 12,
                    "box": vehicles[0].box,
                }
            key = f"plate:{reading.text}"
            if not self.events.allow(key, 150):
                return
            if lookup.get("registered"):
                description = (
                    f"Plate {shown} detected. Registered vehicle: {lookup.get('make') or 'unknown make'} "
                    f"{lookup.get('model') or ''}. Owner: {lookup.get('owner') or 'not recorded'}. "
                    f"Recognition confidence: {reading.confidence:.0%}."
                )
                description_ar = (
                    f"تم قراءة لوحة {shown}. المركبة المسجلة: {lookup.get('make') or 'غير معروفة'} "
                    f"{lookup.get('model') or ''}. المالك: {lookup.get('owner') or 'غير مسجل'}."
                )
                title = f"Vehicle detected: {shown} ({lookup.get('make')} {lookup.get('model')})".strip()
            else:
                description = (
                    f"Plate {shown} detected. The plate is not in the local vehicle registry, so make and model "
                    "are unknown. Add the vehicle on the Vehicles page or configure a vehicle lookup API."
                )
                description_ar = (
                    f"تم قراءة لوحة {shown}. اللوحة غير مسجلة في قاعدة المركبات المحلية، لذلك الشركة والطراز "
                    "غير معروفين. أضف المركبة من صفحة المركبات."
                )
                title = f"Unregistered vehicle plate detected: {shown}"
            self._event(
                "plate",
                "info",
                title,
                description,
                description_ar,
                frame=frame,
                meta={"plate": shown, "confidence": round(reading.confidence, 3), **lookup},
            )
        except Exception:  # noqa: BLE001
            log.exception("Plate scan failed")

    # ---------------------------------------------------------------- events

    def _event(
        self,
        kind: str,
        severity: str,
        title: str,
        description: str,
        description_ar: str = "",
        person: dict | None = None,
        frame: np.ndarray | None = None,
        meta: dict[str, Any] | None = None,
        with_clip: bool = False,
    ) -> dict:
        snapshot_path = ""
        if frame is not None:
            try:
                snapshot = self._annotate(frame.copy())
                snapshot_path = save_jpeg(snapshot, kind)
            except Exception:  # noqa: BLE001
                log.debug("Snapshot save failed", exc_info=True)
        event = self.events.log(
            kind,
            severity,
            title,
            description,
            description_ar=description_ar,
            person=person,
            snapshot_path=snapshot_path,
            meta=meta,
        )
        if event:
            with self._state_lock:
                self._last_event = event
        if event and with_clip:
            frames = list(self._ring)
            if frames:
                self._clip_executor.submit(self._write_clip, frames, kind, int(event["id"]))
        return event

    def _write_clip(self, frames: list[np.ndarray], prefix: str, event_id: int) -> None:
        if not frames:
            return
        path, rel = clip_path(prefix)
        height, width = frames[0].shape[:2]
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 15.0, (width, height))
        actual_rel = rel
        if not writer.isOpened():
            writer.release()
            path = path.with_suffix(".avi")
            writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 15.0, (width, height))
            actual_rel = relative_path(path)
        if not writer.isOpened():
            log.warning("Could not create event clip writer")
            return
        try:
            for frame in frames:
                writer.write(frame)
        finally:
            writer.release()
        self.events.attach_clip(event_id, actual_rel)

    # ---------------------------------------------------------------- overlay

    def _annotate(
        self,
        frame: np.ndarray,
        analysis: FrameAnalysis | None = None,
        faces: list[FaceMatch] | None = None,
        eyewear: dict[int, EyewearResult] | None = None,
        gesture_map: dict[int, tuple[GestureResult, float, tuple[int, int, int, int]]] | None = None,
    ) -> np.ndarray:
        image = frame.copy()
        with self._state_lock:
            analysis = analysis if analysis is not None else self._analysis
            faces = faces if faces is not None else list(self._faces)
            eyewear = eyewear if eyewear is not None else dict(self._eyewear)
            gesture_map = gesture_map if gesture_map is not None else dict(self._gesture_display)
            alarm = dict(self._alarm) if self._alarm and self._alarm.get("until", 0) > time.time() else None
            plate_overlay = dict(self._plate_overlay) if self._plate_overlay and self._plate_overlay.get("until", 0) > time.time() else None
            motion_boxes = list(self._motion_boxes) if self._motion_boxes_until > time.time() else []
            people_count = self._people_count
            known_count = self._known_count
            unknown_count = self._unknown_count

        if analysis is not None:
            for vehicle in analysis.vehicles:
                self._draw_box(image, vehicle.box, _COLORS["vehicle"], f"VEHICLE {vehicle.confidence:.0%}", 1)
            for phone in analysis.phones:
                self._draw_box(image, phone.box, _COLORS["phone"], "PHONE", 1)

            for pose in analysis.poses:
                self._draw_pose(image, pose)
                track_id = pose.track_id if pose.track_id is not None else 0
                gesture_info = gesture_map.get(track_id)
                if gesture_info and gesture_info[0]:
                    gesture, _, box = gesture_info
                    self._draw_box(image, box, _COLORS["gesture"], f"{gesture.name.replace('_', ' ').upper()}", 1)

            for person in analysis.persons:
                person_face = None
                for face in faces:
                    if face.box and _inside(_center(face.box), person.box, pad=20):
                        person_face = face
                        break
                if person_face and person_face.known and person_face.person:
                    label = f"{_ascii(person_face.person['name'])} ({person_face.similarity:.0%})"
                    color = _COLORS["known"]
                else:
                    label = f"UNKNOWN #{person.track_id}" if person.track_id else "PERSON"
                    color = _COLORS["unknown"]
                self._draw_box(image, person.box, color, label, 2)

        for idx, face in enumerate(faces):
            x1, y1, x2, y2 = face.box
            if self._cfg_bool("privacy_blur_unknown", False) and not face.known:
                roi = image[y1:y2, x1:x2]
                if roi.size:
                    kernel = max(9, (min(roi.shape[:2]) // 3) * 2 + 1)
                    if kernel % 2 == 0:
                        kernel += 1
                    image[y1:y2, x1:x2] = cv2.GaussianBlur(roi, (kernel, kernel), 0)
            color = _COLORS["known"] if face.known else _COLORS["unknown"]
            name = _ascii(face.person["name"]) if face.known and face.person else "UNKNOWN"
            glasses = eyewear.get(idx)
            suffix = ""
            if glasses and glasses.detected:
                suffix = " | GLASSES"
            self._draw_box(image, face.box, color, f"{name}{suffix}", 1)

        for box in motion_boxes:
            cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (90, 220, 220), 1)

        if plate_overlay:
            x1, y1, _, _ = plate_overlay["box"]
            text = f"PLATE {plate_overlay['text']}"
            self._draw_box(image, plate_overlay["box"], _COLORS["vehicle"], text, 2)

        top = image.copy()
        cv2.rectangle(top, (0, 0), (image.shape[1], 54), (8, 12, 20), -1)
        image = cv2.addWeighted(top, 0.62, image, 0.38, 0)
        cv2.putText(
            image,
            f"PEOPLE {people_count}   KNOWN {known_count}   UNKNOWN {unknown_count}   UNIQUE {self._unique_seen}",
            (14, 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (210, 235, 245),
            1,
            cv2.LINE_AA,
        )
        status = "DEMO FEED" if self._demo else f"LIVE {self._avg_fps:.0f} FPS"
        cv2.putText(
            image,
            f"{status}   AI {'ON' if self._cfg_bool('ai_enabled', True) else 'OFF'}"
            f"   AUDIO {'ON' if self._cfg_bool('audio_monitor', True) else 'OFF'}",
            (14, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.46,
            (120, 210, 240),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            image,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            (max(10, image.shape[1] - 185), image.shape[0] - 14),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (220, 225, 235),
            1,
            cv2.LINE_AA,
        )
        if self._recording:
            cv2.circle(image, (image.shape[1] - 28, 20), 7, (40, 40, 255), -1)
            cv2.putText(
                image,
                "REC",
                (image.shape[1] - 72, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (80, 80, 255),
                1,
                cv2.LINE_AA,
            )
        if alarm:
            banner_h = 68
            overlay = image.copy()
            cv2.rectangle(overlay, (0, 64), (image.shape[1], 64 + banner_h), (20, 20, 120), -1)
            image = cv2.addWeighted(overlay, 0.75, image, 0.25, 0)
            text = "SECURITY ALERT: " + _ascii(alarm.get("en", ""))[:95]
            cv2.putText(
                image,
                text,
                (16, 96),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.58,
                (60, 220, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                image,
                "AI DETECTION - KEEP DISTANCE - HUMAN VERIFICATION REQUIRED",
                (16, 121),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.44,
                (230, 230, 240),
                1,
                cv2.LINE_AA,
            )
        return image

    @staticmethod
    def _draw_box(
        image: np.ndarray,
        box: tuple[int, int, int, int],
        color: tuple[int, int, int],
        label: str,
        thickness: int = 2,
    ) -> None:
        x1, y1, x2, y2 = box
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
        label = _ascii(label)[:40]
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        y_text = max(14, y1 - 6)
        cv2.rectangle(image, (x1, y_text - th - 4), (x1 + tw + 8, y_text + 3), color, -1)
        text_color = (10, 15, 20) if sum(color) > 380 else (245, 245, 245)
        cv2.putText(image, label, (x1 + 4, y_text), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)

    @staticmethod
    def _draw_pose(image: np.ndarray, pose) -> None:
        points = pose.keypoints
        conf = pose.keypoint_conf
        if points is None:
            return
        for a, b in _COCO_SKELETON:
            if a >= len(points) or b >= len(points):
                continue
            if conf is not None and (conf[a] < 0.3 or conf[b] < 0.3):
                continue
            pa = (int(points[a][0]), int(points[a][1]))
            pb = (int(points[b][0]), int(points[b][1]))
            if pa == (0, 0) or pb == (0, 0):
                continue
            cv2.line(image, pa, pb, _COLORS["pose"], 2, cv2.LINE_AA)
            cv2.circle(image, pa, 3, (230, 230, 255), -1, cv2.LINE_AA)
            cv2.circle(image, pb, 3, (230, 230, 255), -1, cv2.LINE_AA)

    # ---------------------------------------------------------------- public API

    def get_jpeg(self) -> bytes | None:
        with self._frame_lock:
            return self._latest_jpeg

    def latest_raw(self) -> np.ndarray | None:
        with self._frame_lock:
            return None if self._latest_raw is None else self._latest_raw.copy()

    def snapshot_for_event(self, prefix: str = "evidence") -> tuple[str, np.ndarray | None]:
        frame = self.latest_raw()
        if frame is None:
            return "", None
        try:
            annotated = self._annotate(frame.copy())
            path = save_jpeg(annotated, prefix)
            return path, frame
        except Exception:  # noqa: BLE001
            log.debug("snapshot_for_event failed", exc_info=True)
            return "", frame

    def current_known_person(self) -> dict | None:
        with self._state_lock:
            for face in self._faces:
                if face.known and face.person:
                    return dict(face.person)
        return None

    def manual_snapshot(self, note: str = "") -> dict:
        path, _ = self.snapshot_for_event("manual")
        event = self.events.log(
            "snapshot",
            "info",
            "Manual snapshot saved",
            note or "An operator saved a snapshot from the live camera.",
            description_ar="تم حفظ لقطة يدوية من الكاميرا المباشرة.",
            snapshot_path=path,
            meta={"actor": "admin"},
        )
        with self._state_lock:
            self._last_event = event
        return event

    def risk_scan(self) -> dict:
        if not self._cfg_bool("risk_scan_enabled", True):
            raise PermissionError("Risk inspection is disabled in settings.")
        frame = self.latest_raw()
        if frame is None:
            raise RuntimeError("No camera frame is available yet.")
        analysis = self.detector.analyze(frame, run_pose=True)
        faces = self.face_engine.identify(frame, self.face_engine.detect(frame))
        detections = list(analysis.detections)
        if self.threats.custom_available:
            detections.extend(self.threats.scan_custom(frame))
        findings = self.threats.scan(detections, analysis.persons)
        safe = frame.copy()
        for person in analysis.persons:
            x1, y1, x2, y2 = person.box
            roi = safe[y1:y2, x1:x2]
            if roi.size:
                blur = max(31, (min(roi.shape[:2]) // 2) * 2 + 1)
                safe[y1:y2, x1:x2] = cv2.GaussianBlur(roi, (blur, blur), 0)
            cv2.rectangle(safe, (x1, y1), (x2, y2), (110, 170, 200), 2)
            cv2.putText(
                safe,
                "PRIVACY MASK",
                (x1 + 5, max(18, y1 + 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (210, 235, 245),
                1,
                cv2.LINE_AA,
            )
        for finding in findings:
            self._draw_box(safe, finding.box, _COLORS["threat"], f"POSSIBLE {finding.display_label()}", 2)
        cv2.putText(
            safe,
            "PRIVACY-SAFE RISK INSPECTION - NO BODY SCAN",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (90, 220, 255),
            2,
            cv2.LINE_AA,
        )
        path = save_jpeg(safe, "risk_inspection")
        known = [f.person["name"] for f in faces if f.known and f.person]
        item_text = ", ".join(sorted({f.display_label() for f in findings})) or "no restricted visible item"
        event = self.events.log(
            "risk_scan",
            "warning" if findings else "info",
            "Privacy-safe risk inspection performed",
            (
                f"A privacy-safe inspection was run. Visible item result: {item_text}. "
                f"Faces detected: {len(faces)}; registered matches: {', '.join(known) if known else 'none'}. "
                "This mode blurs the body and cannot detect concealed objects. No body imaging, nudity generation, "
                "or fingerprint capture is performed."
            ),
            "تم تنفيذ فحص مخاطر يحمي الخصوصية. لا يقوم النظام بتصوير الجسم أو توليد صور عارية أو أخذ بصمات.",
            snapshot_path=path,
            meta={
                "safe_mode": True,
                "findings": [
                    {"label": f.label, "severity": f.severity, "confidence": round(f.confidence, 3)}
                    for f in findings
                ],
                "known_people": known,
                "no_body_scan": True,
                "advisory": "Human verification required.",
            },
        )
        return {"event": event, "findings": [f.label for f in findings], "known_people": known, "snapshot": path}

    def scan_plate_now(self) -> dict:
        frame = self.latest_raw()
        if frame is None:
            raise RuntimeError("No camera frame available yet.")
        analysis = self.detector.analyze(frame, run_pose=False)
        readings = []
        for vehicle in analysis.vehicles[:3]:
            readings.extend(self.plates.scan_vehicle(frame, vehicle.box))
        if not readings:
            readings = self.plates.scan(frame)
        if not readings:
            return {"plate": "", "registered": False, "message": "No plate could be read. Aim the camera at a clear plate."}
        readings.sort(key=lambda r: r.confidence, reverse=True)
        reading = readings[0]
        lookup = lookup_vehicle(reading.text)
        shown = format_plate(reading.text)
        self._plate_overlay = {"text": shown, "until": time.time() + 15, "box": analysis.vehicles[0].box if analysis.vehicles else (0, 0, frame.shape[1], frame.shape[0])}
        snapshot_path = save_jpeg(self._annotate(frame.copy()), "plate_manual")
        event = self.events.log(
            "plate",
            "info",
            f"Manual plate scan: {shown}",
            (
                f"Manual plate scan read {shown} with {reading.confidence:.0%} confidence. "
                + (
                    f"Registered vehicle: {lookup.get('make')} {lookup.get('model')}, owner {lookup.get('owner')}."
                    if lookup.get("registered")
                    else "Vehicle is not in the local registry."
                )
            ),
            "تم إجراء قراءة يدوية للوحة.",
            snapshot_path=snapshot_path,
            meta={"plate": shown, "confidence": round(reading.confidence, 3), "manual": True, **lookup},
        )
        return {**lookup, "plate": shown, "confidence": round(reading.confidence, 3), "event": event}

    def start_recording(self) -> str:
        with self._record_lock:
            if self._recording:
                return self._recording_rel
            with self._frame_lock:
                frame = None if self._latest_annotated is None else self._latest_annotated.copy()
            if frame is None:
                raise RuntimeError("No frame available yet.")
            path, rel = clip_path("recording")
            writer = cv2.VideoWriter(
                str(path), cv2.VideoWriter_fourcc(*"mp4v"), 15.0, (frame.shape[1], frame.shape[0])
            )
            actual_rel = rel
            if not writer.isOpened():
                writer.release()
                path = path.with_suffix(".avi")
                writer = cv2.VideoWriter(
                    str(path), cv2.VideoWriter_fourcc(*"MJPG"), 15.0, (frame.shape[1], frame.shape[0])
                )
                actual_rel = relative_path(path)
            if not writer.isOpened():
                raise RuntimeError("Could not start the video recorder.")
            self._writer = writer
            self._recording = True
            self._recording_rel = actual_rel
        self.events.log(
            "recording",
            "info",
            "Video recording started",
            "An operator started continuous recording.",
            "بدأ المشغل تسجيل الفيديو المستمر.",
            meta={"path": self._recording_rel},
        )
        return self._recording_rel

    def _stop_recording(self, silent: bool = False) -> str:
        with self._record_lock:
            if not self._recording:
                return self._recording_rel
            self._recording = False
            if self._writer is not None:
                self._writer.release()
                self._writer = None
            rel = self._recording_rel
        if not silent:
            self.events.log(
                "recording",
                "info",
                "Video recording stopped",
                "Continuous recording was stopped and saved.",
                "تم إيقاف تسجيل الفيديو المستمر وحفظه.",
                clip_path=rel,
                meta={"path": rel},
            )
        return rel

    def stop_recording(self) -> str:
        return self._stop_recording()

    def get_status(self) -> dict:
        with self._state_lock:
            alarm = dict(self._alarm) if self._alarm and self._alarm.get("until", 0) > time.time() else None
            last = self._last_event
            last_event = None
            if last:
                last_event = {
                    "id": last.get("id"),
                    "kind": last.get("kind"),
                    "severity": last.get("severity"),
                    "title": last.get("title"),
                    "created_at": last.get("created_at"),
                }
            return {
                "running": self._running,
                "demo": self._demo,
                "source": self._pending_source or self._source_string,
                "width": self._width,
                "height": self._height,
                "fps": round(self._avg_fps, 1),
                "uptime_seconds": int(time.time() - self._started_at),
                "people_count": self._people_count,
                "known_count": self._known_count,
                "unknown_count": self._unknown_count,
                "unique_seen": self._unique_seen,
                "faces_detected": len(self._faces),
                "alarm": alarm,
                "recording": self._recording,
                "recording_path": self._recording_rel if self._recording else "",
                "last_event": last_event,
                "models": {
                    "objects": self.detector.available,
                    "pose": self.detector.pose_available,
                    "faces": self.face_engine.available,
                    "plates": True,
                    "custom_threat_model": self.threats.custom_available,
                },
                "ai_enabled": self._cfg_bool("ai_enabled", True),
            }

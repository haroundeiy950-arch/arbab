from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field

import cv2
import numpy as np

from config import PEOPLE_DIR, SFACE_MODEL, YUNET_MODEL
from core import database as db
from core.storage import absolute_path, relative_path, save_jpeg

log = logging.getLogger(__name__)


@dataclass
class FaceMatch:
    box: tuple[int, int, int, int]
    score: float
    landmarks: np.ndarray
    person: dict | None = None
    similarity: float = 0.0
    embedding: np.ndarray | None = None

    @property
    def known(self) -> bool:
        return self.person is not None


class FaceEngine:
    """YuNet detection + SFace embeddings, stored in the local registry only."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._people: list[dict] = []
        self._embeddings: np.ndarray | None = None
        self._detector = None
        self._recognizer = None
        self._input_size = (0, 0)
        self.available = YUNET_MODEL.exists() and SFACE_MODEL.exists()
        if self.available:
            try:
                self._detector = cv2.FaceDetectorYN.create(
                    str(YUNET_MODEL), "", (320, 320), score_threshold=0.75, nms_threshold=0.3, top_k=5000
                )
                self._recognizer = cv2.FaceRecognizerSF.create(str(SFACE_MODEL), "")
            except Exception as exc:  # noqa: BLE001
                log.error("Could not load face models: %s", exc)
                self.available = False
        self.refresh()

    def refresh(self) -> None:
        with self._lock:
            self._people = db.fetch_all(
                "SELECT id, name, role, company, notes, photo_path, face_embedding, created_at "
                "FROM people WHERE face_embedding IS NOT NULL ORDER BY id"
            )
            vectors = []
            for person in self._people:
                raw = person.get("face_embedding")
                if not raw:
                    continue
                vector = np.frombuffer(raw, dtype=np.float32)
                if vector.size == 128:
                    norm = np.linalg.norm(vector)
                    vectors.append(vector / norm if norm else vector)
            self._embeddings = np.vstack(vectors) if vectors else None
            log.info("Face registry loaded: %d people", len(vectors))

    @property
    def threshold(self) -> float:
        return db.get_float_setting("face_match_threshold", 0.363)

    def detect(self, frame: np.ndarray, min_size: int = 36) -> list[FaceMatch]:
        if not self.available or self._detector is None or self._recognizer is None:
            return []
        h, w = frame.shape[:2]
        with self._lock:
            if self._input_size != (w, h):
                self._detector.setInputSize((w, h))
                self._input_size = (w, h)
            try:
                _, faces = self._detector.detect(frame)
            except cv2.error as exc:
                log.debug("Face detection failed: %s", exc)
                return []
        if faces is None:
            return []
        matches: list[FaceMatch] = []
        for row in faces:
            x, y, fw, fh = (int(v) for v in row[:4])
            score = float(row[14]) if len(row) > 14 else 0.0
            if fw < min_size or fh < min_size or score < 0.75:
                continue
            landmarks = np.asarray(row[4:14], dtype=np.float32)
            box = (max(0, x), max(0, y), min(w, x + fw), min(h, y + fh))
            matches.append(FaceMatch(box=box, score=score, landmarks=landmarks))
        matches.sort(key=lambda m: (m.box[2] - m.box[0]) * (m.box[3] - m.box[1]), reverse=True)
        return matches

    def _embedding(self, frame: np.ndarray, face: FaceMatch) -> np.ndarray | None:
        if self._recognizer is None:
            return None
        with self._lock:
            try:
                row = np.array(
                    [*face.box, *face.landmarks.tolist(), face.score], dtype=np.float32
                ).reshape(1, -1)
                aligned = self._recognizer.alignCrop(frame, row)
                feature = self._recognizer.feature(aligned).astype(np.float32).ravel()
                if feature.size != 128:
                    return None
                norm = np.linalg.norm(feature)
                return feature / norm if norm else None
            except cv2.error as exc:
                log.debug("Face embedding failed: %s", exc)
                return None

    def identify(self, frame: np.ndarray, faces: list[FaceMatch] | None = None) -> list[FaceMatch]:
        faces = faces if faces is not None else self.detect(frame)
        with self._lock:
            people = list(self._people)
            embeddings = self._embeddings
        threshold = self.threshold
        for face in faces:
            embedding = self._embedding(frame, face)
            face.embedding = embedding
            if embedding is None or embeddings is None:
                continue
            similarities = embeddings @ embedding
            best = int(np.argmax(similarities))
            best_score = float(similarities[best])
            face.similarity = best_score
            if best_score >= threshold and best < len(people):
                face.person = people[best]
        return faces

    @staticmethod
    def crop_with_margin(frame: np.ndarray, face: FaceMatch, margin: float = 0.25) -> np.ndarray:
        x1, y1, x2, y2 = face.box
        w, h = x2 - x1, y2 - y1
        mx, my = int(w * margin), int(h * margin)
        H, W = frame.shape[:2]
        crop = frame[max(0, y1 - my) : min(H, y2 + my), max(0, x1 - mx) : min(W, x2 + mx)]
        return crop

    def register(
        self,
        frame: np.ndarray,
        name: str,
        role: str = "",
        company: str = "",
        notes: str = "",
        consent: bool = True,
    ) -> dict:
        if not self.available:
            raise RuntimeError("Face models are not available. Run setup.ps1 to download them.")
        faces = self.detect(frame)
        if not faces:
            raise ValueError("No clear face was found. Look at the camera in good light and try again.")
        face = faces[0]
        embedding = self._embedding(frame, face)
        if embedding is None:
            raise ValueError("Could not read the face. Try again with a clearer image.")
        crop = self.crop_with_margin(frame, face)
        if crop.size == 0:
            raise ValueError("Invalid face crop.")
        crop = cv2.resize(crop, (320, 320), interpolation=cv2.INTER_AREA)
        photo_rel = save_jpeg(crop, name or "person", folder=PEOPLE_DIR, quality=92)
        now = db.utcnow()
        person_id = db.execute(
            "INSERT INTO people(name, role, company, notes, consent, photo_path, face_embedding, "
            "created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                name.strip()[:120] or "Unnamed",
                role.strip()[:120],
                company.strip()[:120],
                notes.strip()[:2000],
                1 if consent else 0,
                photo_rel,
                embedding.astype(np.float32).tobytes(),
                now,
                now,
            ),
        )
        self.refresh()
        db.log_audit("person_registered", f"id={person_id} name={name}", actor="admin")
        person = db.fetch_one("SELECT * FROM people WHERE id = ?", (person_id,))
        return db.row_to_public(person) or {}

    def register_from_upload(
        self, image_bytes: bytes, name: str, role: str = "", company: str = "", notes: str = "", consent: bool = True
    ) -> dict:
        image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("The uploaded file is not a valid image.")
        return self.register(image, name, role, company, notes, consent)

    def delete(self, person_id: int) -> bool:
        person = db.fetch_one("SELECT * FROM people WHERE id = ?", (person_id,))
        if not person:
            return False
        db.execute("DELETE FROM people WHERE id = ?", (person_id,))
        if person.get("photo_path"):
            try:
                absolute_path(person["photo_path"]).unlink(missing_ok=True)
            except (ValueError, OSError):
                pass
        self.refresh()
        db.log_audit("person_deleted", f"id={person_id} name={person.get('name')}", actor="admin")
        return True

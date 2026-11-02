from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from config import AUDIO_DIR, CLIP_DIR, DATA_DIR, PEOPLE_DIR, SNAPSHOT_DIR


def _safe_stem(prefix: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_-]+", "-", prefix).strip("-") or "item"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{clean}_{stamp}_{uuid.uuid4().hex[:6]}"


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(DATA_DIR.resolve()).as_posix()
    except ValueError:
        return path.name


def absolute_path(relative: str) -> Path:
    candidate = (DATA_DIR / relative).resolve()
    if not str(candidate).startswith(str(DATA_DIR.resolve())):
        raise ValueError("Path escapes data directory")
    return candidate


def save_jpeg(image: np.ndarray, prefix: str, folder: Path = SNAPSHOT_DIR, quality: int = 90) -> str:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{_safe_stem(prefix)}.jpg"
    cv2.imwrite(str(path), image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    return relative_path(path)


def save_upload(data: bytes, filename: str, folder: Path = PEOPLE_DIR) -> str:
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"
    path = folder / f"{_safe_stem('upload')}{suffix}"
    path.write_bytes(data)
    image = cv2.imread(str(path))
    if image is not None and suffix != ".jpg":
        jpg_path = path.with_suffix(".jpg")
        cv2.imwrite(str(jpg_path), image, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        path.unlink(missing_ok=True)
        path = jpg_path
    return relative_path(path)


def save_audio(data: bytes, prefix: str = "speech") -> str:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    path = AUDIO_DIR / f"{_safe_stem(prefix)}.wav"
    path.write_bytes(data)
    return relative_path(path)


def clip_path(prefix: str) -> tuple[Path, str]:
    CLIP_DIR.mkdir(parents=True, exist_ok=True)
    path = CLIP_DIR / f"{_safe_stem(prefix)}.mp4"
    return path, relative_path(path)


def save_bytes(data: bytes, relative: str) -> Path:
    path = absolute_path(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def delete_media(relative: str | None) -> None:
    if not relative:
        return
    try:
        path = absolute_path(relative)
        path.unlink(missing_ok=True)
    except (ValueError, OSError):
        pass

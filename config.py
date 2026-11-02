from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = Path(os.getenv("SENTINEL_DATA_DIR", BASE_DIR / "data")).resolve()
MODELS_DIR = Path(os.getenv("SENTINEL_MODELS_DIR", BASE_DIR / "models")).resolve()

SNAPSHOT_DIR = DATA_DIR / "snapshots"
CLIP_DIR = DATA_DIR / "clips"
AUDIO_DIR = DATA_DIR / "audio"
PEOPLE_DIR = DATA_DIR / "people"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
LOG_DIR = DATA_DIR / "logs"

for _dir in (DATA_DIR, MODELS_DIR, SNAPSHOT_DIR, CLIP_DIR, AUDIO_DIR, PEOPLE_DIR, KNOWLEDGE_DIR, LOG_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(os.getenv("SENTINEL_DB", DATA_DIR / "sentinel.db"))
YUNET_MODEL = MODELS_DIR / "face_detection_yunet.onnx"
SFACE_MODEL = MODELS_DIR / "face_recognition_sface.onnx"
YOLO_MODEL = MODELS_DIR / "yolov8n.pt"
POSE_MODEL = MODELS_DIR / "yolov8n-pose.pt"
WEAPON_MODEL = MODELS_DIR / "weapon.pt"

APP_NAME = "Arbab Sentinel AI Camera"
APP_VERSION = "1.0.0"

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeMe-Now!123")

HOST = os.getenv("SENTINEL_HOST", "127.0.0.1")
PORT = int(os.getenv("SENTINEL_PORT", "8000"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip() or None
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
LIBRETRANSLATE_URL = os.getenv("LIBRETRANSLATE_URL", "").strip()
VEHICLE_LOOKUP_URL = os.getenv("VEHICLE_LOOKUP_URL", "").strip()
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny").strip()

DEFAULT_SETTINGS: dict[str, str] = {
    "camera_source": os.getenv("CAMERA_SOURCE", "0"),
    "frame_width": "960",
    "frame_height": "540",
    "ai_enabled": "1",
    "face_recognition": "1",
    "face_match_threshold": "0.363",
    "person_confidence": "0.35",
    "count_persons": "1",
    "gesture_recognition": "1",
    "plate_recognition": "1",
    "threat_detection": "1",
    "glasses_detection": "1",
    "audio_monitor": "1",
    "transcribe_audio": "1",
    "translate_events": "1",
    "auto_save_motion": "1",
    "motion_threshold": "0.025",
    "alarm_enabled": "1",
    "alert_unknown_person": "1",
    "restricted_classes": "knife,scissors,baseball bat",
    "smart_glasses_alerts": "0",
    "privacy_blur_unknown": "0",
    "auto_answer_questions": "1",
    "retention_days": "14",
    "translation_targets": "en,ar",
    "company_name": "Arbab Company",
    "notification_language": "en",
    "detection_interval": "0.35",
    "audio_threshold": "450",
    "risk_scan_enabled": "1",
    "llm_enabled": "1" if OPENAI_API_KEY else "0",
    "session_timeout_minutes": "720",
}

GESTURE_ALERTS = "1"


def get_secret_key() -> str:
    env_secret = os.getenv("SENTINEL_SECRET_KEY", "").strip()
    if env_secret:
        return env_secret
    secret_file = DATA_DIR / "secret.key"
    if secret_file.exists():
        value = secret_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    value = secrets.token_urlsafe(48)
    secret_file.write_text(value, encoding="utf-8")
    try:
        os.chmod(secret_file, 0o600)
    except OSError:
        pass
    return value

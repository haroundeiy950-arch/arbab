from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field

from ai.agent import SecurityAgent
from ai.face import FaceEngine
from ai.knowledge import KnowledgeBase
from ai.translate import TranslationService
from config import APP_NAME, APP_VERSION
from core import database as db
from core.events import EventManager
from services.audio_service import AudioService
from services.camera_service import CameraService
from web.alerts import AlertHub

log = logging.getLogger(__name__)


@dataclass
class Runtime:
    translator: TranslationService
    knowledge: KnowledgeBase
    agent: SecurityAgent
    events: EventManager
    face: FaceEngine
    camera: CameraService
    audio: AudioService
    hub: AlertHub
    started_at: float = field(default_factory=time.time)
    _cleanup_stop: threading.Event = field(default_factory=threading.Event)
    _cleanup_thread: threading.Thread | None = None

    def start(self) -> None:
        self.camera.start()
        self.audio.start()
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, name="retention", daemon=True)
        self._cleanup_thread.start()

    def _cleanup_loop(self) -> None:
        while not self._cleanup_stop.wait(6 * 3600):
            try:
                self.events.cleanup()
            except Exception:  # noqa: BLE001
                log.exception("Retention cleanup failed")

    def status(self) -> dict:
        audio_status = self.audio.get_status()
        stats = self.events.stats()
        recent = self.events.list(limit=8)
        return {
            "app": {"name": APP_NAME, "version": APP_VERSION, "server_time": db.utcnow()},
            "camera": self.camera.get_status(),
            "audio": audio_status,
            "events": stats,
            "recent_events": recent,
            "agent": {
                "provider": self.agent.provider,
                "llm_configured": self.agent.enabled,
                "knowledge_chunks": len(self.knowledge.chunks),
            },
            "translation": {"last_error": self.translator.last_error},
            "uptime_seconds": int(time.time() - self.started_at),
        }

    def shutdown(self) -> None:
        self._cleanup_stop.set()
        try:
            self.audio.stop()
        finally:
            self.camera.stop()
            self.events.shutdown()

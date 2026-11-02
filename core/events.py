from __future__ import annotations

import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from ai.translate import TranslationService
from core import database as db
from core.storage import delete_media

log = logging.getLogger(__name__)


class EventManager:
    def __init__(
        self,
        translator: TranslationService,
        publish: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.translator = translator
        self.publish = publish
        self._cooldowns: dict[str, float] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="event-i18n")

    def allow(self, key: str, seconds: float) -> bool:
        import time

        now = time.monotonic()
        with self._lock:
            previous = self._cooldowns.get(key, 0.0)
            if now - previous < seconds:
                return False
            self._cooldowns[key] = now
            return True

    def _row(self, event_id: int) -> dict[str, Any] | None:
        row = db.fetch_one("SELECT * FROM events WHERE id = ?", (event_id,))
        if not row:
            return None
        row["meta"] = db.event_meta(row)
        return row

    def log(
        self,
        kind: str,
        severity: str,
        title: str,
        description: str = "",
        description_ar: str = "",
        person: dict[str, Any] | None = None,
        snapshot_path: str = "",
        clip_path: str = "",
        audio_path: str = "",
        transcript: str = "",
        translation: str = "",
        meta: dict[str, Any] | None = None,
        translate: bool = True,
        cooldown_key: str | None = None,
        cooldown_seconds: float = 0.0,
    ) -> dict[str, Any]:
        if cooldown_key and cooldown_seconds > 0 and not self.allow(cooldown_key, cooldown_seconds):
            return {}
        person_id = int(person["id"]) if person and person.get("id") else None
        person_name = str(person.get("name", "")) if person else ""
        meta = meta or {}
        meta.setdefault("created_by", "ai-camera")
        event_id = db.execute(
            "INSERT INTO events(kind, severity, title, description, description_ar, person_id, person_name, "
            "snapshot_path, clip_path, audio_path, transcript, translation, meta, created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                kind,
                severity,
                title[:300],
                description[:8000],
                description_ar[:8000],
                person_id,
                person_name[:120],
                snapshot_path,
                clip_path,
                audio_path,
                transcript[:8000],
                translation[:8000],
                json.dumps(meta, ensure_ascii=False, default=str)[:12000],
                db.utcnow(),
            ),
        )
        event = self._row(event_id)
        if event and self.publish:
            try:
                self.publish(event)
            except Exception:  # noqa: BLE001
                log.debug("Event publish failed", exc_info=True)
        if (
            event
            and translate
            and description
            and not description_ar
            and db.get_bool_setting("translate_events", True)
        ):
            self._executor.submit(self._translate_event_async, event_id, description)
        return event or {}

    def _translate_event_async(self, event_id: int, text: str) -> None:
        try:
            translated = self.translator.translate(text, target="ar", source="en")
            if not translated or translated == text:
                return
            db.execute("UPDATE events SET description_ar = ? WHERE id = ?", (translated[:8000], event_id))
            event = self._row(event_id)
            if event and self.publish:
                self.publish(event)
        except Exception as exc:  # noqa: BLE001
            log.debug("Background event translation failed: %s", exc)

    def attach_clip(self, event_id: int, clip_path: str) -> None:
        db.execute("UPDATE events SET clip_path = ? WHERE id = ?", (clip_path, event_id))
        event = self._row(event_id)
        if event and self.publish:
            try:
                self.publish(event)
            except Exception:  # noqa: BLE001
                log.debug("Clip publish failed", exc_info=True)

    def acknowledge(self, event_id: int) -> bool:
        event = self._row(event_id)
        if not event:
            return False
        db.execute("UPDATE events SET acknowledged = 1 WHERE id = ?", (event_id,))
        updated = self._row(event_id)
        if updated and self.publish:
            self.publish(updated)
        return True

    def delete(self, event_id: int) -> bool:
        event = self._row(event_id)
        if not event:
            return False
        for key in ("snapshot_path", "clip_path", "audio_path"):
            delete_media(event.get(key))
        db.execute("DELETE FROM events WHERE id = ?", (event_id,))
        return True

    def get(self, event_id: int) -> dict[str, Any] | None:
        return self._row(event_id)

    def list(
        self,
        kind: str = "",
        severity: str = "",
        limit: int = 50,
        offset: int = 0,
        search: str = "",
    ) -> list[dict[str, Any]]:
        clause = "WHERE 1=1"
        params: list[Any] = []
        if kind:
            clause += " AND kind = ?"
            params.append(kind)
        if severity:
            clause += " AND severity = ?"
            params.append(severity)
        if search:
            clause += " AND (title LIKE ? OR description LIKE ? OR person_name LIKE ? OR transcript LIKE ?)"
            needle = f"%{search}%"
            params.extend([needle, needle, needle, needle])
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        rows = db.fetch_all(
            f"SELECT * FROM events {clause} ORDER BY id DESC LIMIT ? OFFSET ?", params
        )
        for row in rows:
            row["meta"] = db.event_meta(row)
        return rows

    def cleanup(self, retention_days: int | None = None) -> int:
        days = retention_days or db.get_int_setting("retention_days", 14)
        cutoff = db.utcnow()[:10]
        from datetime import datetime, timedelta, timezone

        cutoff_dt = datetime.now(timezone.utc) - timedelta(days=max(1, days))
        cutoff_iso = cutoff_dt.isoformat(timespec="seconds")
        rows = db.fetch_all("SELECT * FROM events WHERE created_at < ? LIMIT 500", (cutoff_iso,))
        for row in rows:
            for key in ("snapshot_path", "clip_path", "audio_path"):
                delete_media(row.get(key))
            db.execute("DELETE FROM events WHERE id = ?", (row["id"],))
        if rows:
            log.info("Event retention removed %d rows (cutoff %s, date %s)", len(rows), cutoff_iso, cutoff)
        return len(rows)

    def stats(self) -> dict[str, Any]:
        from datetime import datetime, timedelta, timezone

        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(timespec="seconds")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        row = db.fetch_one(
            "SELECT "
            "(SELECT COUNT(*) FROM events WHERE created_at >= ?) AS last24, "
            "(SELECT COUNT(*) FROM events WHERE created_at >= ? AND severity='critical') AS critical24, "
            "(SELECT COUNT(*) FROM events WHERE created_at >= ? AND severity='warning') AS warning24, "
            "(SELECT COUNT(*) FROM events WHERE created_at LIKE ?) AS today, "
            "(SELECT COUNT(*) FROM events WHERE acknowledged=0 AND severity IN ('warning','critical')) AS unack, "
            "(SELECT COUNT(*) FROM events WHERE kind='speech' AND created_at >= ?) AS speech24, "
            "(SELECT COUNT(*) FROM events WHERE kind='plate' AND created_at >= ?) AS plates24, "
            "(SELECT COUNT(*) FROM people) AS people, "
            "(SELECT COUNT(*) FROM vehicles) AS vehicles",
            (since, since, since, f"{today}%", since, since),
        )
        return row or {}

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

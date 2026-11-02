from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Iterable

from config import ADMIN_PASSWORD, ADMIN_USERNAME, DB_PATH, DEFAULT_SETTINGS

_LOCK = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT DEFAULT '',
    company TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    consent INTEGER DEFAULT 0,
    photo_path TEXT DEFAULT '',
    face_embedding BLOB,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info',
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    description_ar TEXT DEFAULT '',
    person_id INTEGER,
    person_name TEXT DEFAULT '',
    snapshot_path TEXT DEFAULT '',
    clip_path TEXT DEFAULT '',
    audio_path TEXT DEFAULT '',
    transcript TEXT DEFAULT '',
    translation TEXT DEFAULT '',
    meta TEXT DEFAULT '{}',
    acknowledged INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind);
CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity);

CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate TEXT NOT NULL UNIQUE,
    make TEXT DEFAULT '',
    model TEXT DEFAULT '',
    color TEXT DEFAULT '',
    owner TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    photo_path TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT DEFAULT '',
    action TEXT NOT NULL,
    detail TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources TEXT DEFAULT '',
    provider TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def fetch_all(sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    with _LOCK:
        conn = get_connection()
        try:
            rows = conn.execute(sql, tuple(params)).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()


def fetch_one(sql: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def scalar(sql: str, params: Iterable[Any] = (), default: Any = None) -> Any:
    row = fetch_one(sql, params)
    if not row:
        return default
    return next(iter(row.values()))


def execute(sql: str, params: Iterable[Any] = ()) -> int:
    with _LOCK:
        conn = get_connection()
        try:
            cur = conn.execute(sql, tuple(params))
            conn.commit()
            return int(cur.lastrowid or 0)
        finally:
            conn.close()


def execute_many(sql: str, seq_params: Iterable[Iterable[Any]]) -> None:
    with _LOCK:
        conn = get_connection()
        try:
            conn.executemany(sql, [tuple(p) for p in seq_params])
            conn.commit()
        finally:
            conn.close()


def init_db() -> None:
    with _LOCK:
        conn = get_connection()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
            for key, value in DEFAULT_SETTINGS.items():
                conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES(?, ?)", (key, value))
            conn.commit()
            existing = conn.execute("SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,)).fetchone()
            if not existing:
                from core.security import hash_password

                conn.execute(
                    "INSERT INTO users(username, password_hash, created_at) VALUES(?, ?, ?)",
                    (ADMIN_USERNAME, hash_password(ADMIN_PASSWORD), utcnow()),
                )
                conn.commit()
        finally:
            conn.close()


def get_setting(key: str, default: str = "") -> str:
    row = fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
    return row["value"] if row else default


def get_bool_setting(key: str, default: bool = False) -> bool:
    value = get_setting(key, "1" if default else "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def get_float_setting(key: str, default: float) -> float:
    try:
        return float(get_setting(key, str(default)))
    except (TypeError, ValueError):
        return default


def get_int_setting(key: str, default: int) -> int:
    try:
        return int(float(get_setting(key, str(default))))
    except (TypeError, ValueError):
        return default


def set_setting(key: str, value: Any) -> None:
    execute(
        "INSERT INTO settings(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )


def all_settings() -> dict[str, str]:
    return {row["key"]: row["value"] for row in fetch_all("SELECT key, value FROM settings")}


def log_audit(action: str, detail: str = "", actor: str = "system") -> None:
    execute(
        "INSERT INTO audit_log(actor, action, detail, created_at) VALUES(?, ?, ?, ?)",
        (actor, action, detail[:4000], utcnow()),
    )


def event_meta(row: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(row.get("meta") or "{}")
    except (TypeError, ValueError):
        return {}


def row_to_public(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: v for k, v in row.items() if k != "face_embedding" and k != "password_hash"}

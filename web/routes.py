from __future__ import annotations

import asyncio
import mimetypes
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from ai.plates import normalize_plate
from config import (
    APP_NAME,
    APP_VERSION,
    DATA_DIR,
    DEFAULT_SETTINGS,
    KNOWLEDGE_DIR,
    OPENAI_API_KEY,
)
from core import database as db
from core.security import hash_password, verify_password
from core.storage import absolute_path
from web.alerts import AlertHub

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

_LOGIN_ATTEMPTS: dict[str, list[float]] = {}
_LOGIN_WINDOW = 300
_LOGIN_MAX = 8

SETTING_KEYS = set(DEFAULT_SETTINGS) | {
    "whisper_model",
    "audio_device",
}


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _login_limited(ip: str) -> bool:
    now = time.time()
    attempts = [t for t in _LOGIN_ATTEMPTS.get(ip, []) if now - t < _LOGIN_WINDOW]
    _LOGIN_ATTEMPTS[ip] = attempts
    return len(attempts) >= _LOGIN_MAX


def _record_login_failure(ip: str) -> None:
    _LOGIN_ATTEMPTS.setdefault(ip, []).append(time.time())


def _runtime(request: Request):
    runtime = getattr(request.app.state, "runtime", None)
    if runtime is None:
        raise HTTPException(status_code=503, detail="Services are still starting.")
    return runtime


def _ctx(request: Request, page: str, title: str, **extra: Any) -> dict[str, Any]:
    return {
        "request": request,
        "page": page,
        "title": title,
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "username": request.session.get("user", ""),
        **extra,
    }


def _media_url(relative: str | None) -> str:
    if not relative:
        return ""
    return "/media/" + quote(relative.replace("\\", "/"))


def _serialize_person(row: dict[str, Any]) -> dict[str, Any]:
    data = db.row_to_public(row) or {}
    data["photo_url"] = _media_url(data.get("photo_path"))
    return data


def _serialize_event(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    data = dict(row)
    if isinstance(data.get("meta"), str):
        data["meta"] = db.event_meta(data)
    data["snapshot_url"] = _media_url(data.get("snapshot_path"))
    data["clip_url"] = _media_url(data.get("clip_path"))
    data["audio_url"] = _media_url(data.get("audio_path"))
    return data


def _sanitize_knowledge_name(name: str) -> str:
    base = Path(name or "").name
    if not base or base in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid document name")
    return base


async def _read_upload(upload, max_bytes: int = 20 * 1024 * 1024) -> bytes:
    data = await upload.read()
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="File is too large")
    return data


# --------------------------------------------------------------------- pages


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    if request.session.get("user"):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": error, "app_name": APP_NAME})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request):
    ip = _client_ip(request)
    if _login_limited(ip):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Too many attempts. Wait a few minutes and try again.", "app_name": APP_NAME},
            status_code=429,
        )
    form = await request.form()
    username = str(form.get("username", "")).strip()
    password = str(form.get("password", ""))
    user = db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
    if user and verify_password(password, user["password_hash"]):
        request.session.clear()
        request.session["user"] = username
        request.session["login_at"] = int(time.time())
        _LOGIN_ATTEMPTS.pop(ip, None)
        db.log_audit("login_success", f"ip={ip}", actor=username)
        return RedirectResponse("/", status_code=303)
    _record_login_failure(ip)
    db.log_audit("login_failure", f"username={username} ip={ip}", actor="anonymous")
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": "Invalid username or password.", "app_name": APP_NAME, "username": username},
        status_code=401,
    )


@router.get("/logout")
async def logout(request: Request):
    username = request.session.get("user", "")
    request.session.clear()
    db.log_audit("logout", actor=username)
    return RedirectResponse("/login", status_code=303)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", _ctx(request, "dashboard", "Live Dashboard"))


@router.get("/events", response_class=HTMLResponse)
async def events_page(request: Request):
    return templates.TemplateResponse(request, "events.html", _ctx(request, "events", "Event Evidence"))


@router.get("/people", response_class=HTMLResponse)
async def people_page(request: Request):
    return templates.TemplateResponse(request, "people.html", _ctx(request, "people", "People Registry"))


@router.get("/vehicles", response_class=HTMLResponse)
async def vehicles_page(request: Request):
    return templates.TemplateResponse(request, "vehicles.html", _ctx(request, "vehicles", "Vehicle Registry"))


@router.get("/knowledge", response_class=HTMLResponse)
async def knowledge_page(request: Request):
    return templates.TemplateResponse(request, "knowledge.html", _ctx(request, "knowledge", "Knowledge Base"))


@router.get("/assistant", response_class=HTMLResponse)
async def assistant_page(request: Request):
    return templates.TemplateResponse(request, "assistant.html", _ctx(request, "assistant", "AI Assistant"))


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse(request, "settings.html", _ctx(request, "settings", "Settings"))


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse(request, "about.html", _ctx(request, "about", "Safety & Limitations"))


# ------------------------------------------------------------------- streams


@router.get("/video_feed")
async def video_feed(request: Request):
    runtime = _runtime(request)

    async def generator():
        while True:
            jpeg = runtime.camera.get_jpeg()
            if jpeg:
                yield (
                    b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                    + str(len(jpeg)).encode("ascii")
                    + b"\r\n\r\n"
                    + jpeg
                    + b"\r\n"
                )
            await asyncio.sleep(0.055)

    return StreamingResponse(
        generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"},
    )


@router.websocket("/ws/alerts")
async def alerts_ws(websocket: WebSocket):
    try:
        user = websocket.session.get("user")
    except Exception:  # noqa: BLE001
        user = None
    if not user:
        await websocket.close(code=1008)
        return
    hub: AlertHub = websocket.app.state.runtime.hub
    await hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(websocket)
    except Exception:  # noqa: BLE001
        hub.disconnect(websocket)


@router.get("/media/{path:path}")
async def media(path: str):
    try:
        file_path = absolute_path(path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid media path")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Media not found")
    content_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        file_path,
        media_type=content_type or "application/octet-stream",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


# ---------------------------------------------------------------------- APIs


@router.get("/api/status")
async def api_status(request: Request):
    runtime = _runtime(request)
    status = runtime.status()
    status["recent_events"] = [_serialize_event(e) for e in status.get("recent_events", [])]
    camera = status.get("camera", {})
    if camera.get("last_event"):
        camera["last_event"] = dict(camera["last_event"])
    return JSONResponse(status)


@router.get("/api/stats")
async def api_stats(request: Request):
    runtime = _runtime(request)
    stats = runtime.events.stats()
    stats.update(
        {
            "people_count": runtime.camera.get_status().get("people_count", 0),
            "known_count": runtime.camera.get_status().get("known_count", 0),
            "unknown_count": runtime.camera.get_status().get("unknown_count", 0),
            "unique_seen": runtime.camera.get_status().get("unique_seen", 0),
            "recording": runtime.camera.get_status().get("recording", False),
        }
    )
    return stats


@router.get("/api/events")
async def api_events(
    request: Request,
    kind: str = "",
    severity: str = "",
    search: str = "",
    limit: int = 40,
    offset: int = 0,
):
    runtime = _runtime(request)
    limit = max(1, min(limit, 200))
    rows = runtime.events.list(kind=kind, severity=severity, limit=limit + 1, offset=max(0, offset), search=search)
    has_more = len(rows) > limit
    rows = rows[:limit]
    return {"events": [_serialize_event(row) for row in rows], "has_more": has_more, "offset": offset}


@router.get("/api/events/{event_id}")
async def api_event(request: Request, event_id: int):
    runtime = _runtime(request)
    event = runtime.events.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return _serialize_event(event)


@router.post("/api/events/{event_id}/ack")
async def api_event_ack(request: Request, event_id: int):
    runtime = _runtime(request)
    if not runtime.events.acknowledge(event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    db.log_audit("event_acknowledged", f"id={event_id}", actor=request.session.get("user", ""))
    return {"ok": True}


@router.delete("/api/events/{event_id}")
async def api_event_delete(request: Request, event_id: int):
    runtime = _runtime(request)
    if not runtime.events.delete(event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    db.log_audit("event_deleted", f"id={event_id}", actor=request.session.get("user", ""))
    return {"ok": True}


@router.post("/api/snapshot")
async def api_snapshot(request: Request):
    runtime = _runtime(request)
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        payload = {}
    note = str((payload or {}).get("note", ""))[:400]
    event = runtime.camera.manual_snapshot(note)
    db.log_audit("manual_snapshot", f"event={event.get('id')}", actor=request.session.get("user", ""))
    return {"ok": True, "event": _serialize_event(event)}


@router.post("/api/recording/start")
async def api_recording_start(request: Request):
    runtime = _runtime(request)
    try:
        path = runtime.camera.start_recording()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.log_audit("recording_started", path, actor=request.session.get("user", ""))
    return {"ok": True, "path": path}


@router.post("/api/recording/stop")
async def api_recording_stop(request: Request):
    runtime = _runtime(request)
    path = runtime.camera.stop_recording()
    db.log_audit("recording_stopped", path, actor=request.session.get("user", ""))
    return {"ok": True, "path": path, "url": _media_url(path)}


@router.post("/api/risk_scan")
async def api_risk_scan(request: Request):
    runtime = _runtime(request)
    try:
        result = await run_in_threadpool(runtime.camera.risk_scan)
    except (RuntimeError, PermissionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.log_audit("risk_scan", "privacy-safe inspection", actor=request.session.get("user", ""))
    result["event"] = _serialize_event(result.get("event"))
    return result


@router.post("/api/scan/plate")
async def api_scan_plate(request: Request):
    runtime = _runtime(request)
    try:
        result = await run_in_threadpool(runtime.camera.scan_plate_now)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    result["event"] = _serialize_event(result.get("event"))
    db.log_audit("plate_scan", result.get("plate", ""), actor=request.session.get("user", ""))
    return result


# --------------------------------------------------------------------- people


@router.get("/api/people")
async def api_people(request: Request):
    rows = db.fetch_all("SELECT * FROM people ORDER BY id DESC")
    return {"people": [_serialize_person(row) for row in rows]}


@router.post("/api/people")
async def api_people_create(request: Request):
    runtime = _runtime(request)
    form = await request.form()
    name = str(form.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    consent = str(form.get("consent", "")).lower() in {"1", "true", "on", "yes"}
    if not consent:
        raise HTTPException(
            status_code=400,
            detail="Consent is required before registering a face. The person must agree to local face recognition.",
        )
    role = str(form.get("role", ""))[:120]
    company = str(form.get("company", ""))[:120]
    notes = str(form.get("notes", ""))[:2000]
    photo = form.get("photo")
    try:
        if photo is not None and getattr(photo, "filename", ""):
            data = await _read_upload(photo, 15 * 1024 * 1024)
            person = await run_in_threadpool(
                runtime.face.register_from_upload, data, name, role, company, notes, consent
            )
        else:
            frame = runtime.camera.latest_raw()
            if frame is None:
                raise HTTPException(status_code=400, detail="No camera frame available. Upload a photo instead.")
            person = await run_in_threadpool(
                runtime.face.register, frame, name, role, company, notes, consent
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.log_audit("person_registered", f"id={person.get('id')} name={name}", actor=request.session.get("user", ""))
    return {"ok": True, "person": _serialize_person(person)}


@router.delete("/api/people/{person_id}")
async def api_people_delete(request: Request, person_id: int):
    runtime = _runtime(request)
    if not runtime.face.delete(person_id):
        raise HTTPException(status_code=404, detail="Person not found")
    db.log_audit("person_deleted", f"id={person_id}", actor=request.session.get("user", ""))
    return {"ok": True}


# ------------------------------------------------------------------- vehicles


@router.get("/api/vehicles")
async def api_vehicles(request: Request):
    rows = db.fetch_all("SELECT * FROM vehicles ORDER BY id DESC")
    for row in rows:
        row["photo_url"] = _media_url(row.get("photo_path"))
    return {"vehicles": rows}


@router.post("/api/vehicles")
async def api_vehicles_create(request: Request):
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    plate = normalize_plate(str(payload.get("plate", "")))
    if len(plate) < 3:
        raise HTTPException(status_code=400, detail="A valid plate is required")
    make = str(payload.get("make", "")).strip()[:80]
    model = str(payload.get("model", "")).strip()[:80]
    color = str(payload.get("color", "")).strip()[:40]
    owner = str(payload.get("owner", "")).strip()[:120]
    notes = str(payload.get("notes", "")).strip()[:1000]
    db.execute(
        "INSERT INTO vehicles(plate, make, model, color, owner, notes, created_at) VALUES(?,?,?,?,?,?,?) "
        "ON CONFLICT(plate) DO UPDATE SET make=excluded.make, model=excluded.model, color=excluded.color, "
        "owner=excluded.owner, notes=excluded.notes",
        (plate, make, model, color, owner, notes, db.utcnow()),
    )
    db.log_audit("vehicle_saved", f"plate={plate}", actor=request.session.get("user", ""))
    row = db.fetch_one("SELECT * FROM vehicles WHERE plate = ?", (plate,))
    return {"ok": True, "vehicle": row}


@router.delete("/api/vehicles/{vehicle_id}")
async def api_vehicles_delete(request: Request, vehicle_id: int):
    row = db.fetch_one("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
    db.log_audit("vehicle_deleted", f"plate={row.get('plate')}", actor=request.session.get("user", ""))
    return {"ok": True}


# ------------------------------------------------------------------ knowledge


@router.get("/api/knowledge")
async def api_knowledge(request: Request):
    runtime = _runtime(request)
    docs = []
    for path in sorted(KNOWLEDGE_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".pdf"}:
            docs.append(
                {
                    "name": path.name,
                    "size": path.stat().st_size,
                    "editable": path.suffix.lower() in {".md", ".txt"},
                    "updated": time.strftime("%Y-%m-%d %H:%M", time.localtime(path.stat().st_mtime)),
                }
            )
    return {"stats": runtime.knowledge.stats(), "docs": docs}


@router.get("/api/knowledge/doc")
async def api_knowledge_doc(request: Request, name: str):
    safe_name = _sanitize_knowledge_name(name)
    path = (KNOWLEDGE_DIR / safe_name).resolve()
    if not str(path).startswith(str(KNOWLEDGE_DIR.resolve())) or not path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    if path.suffix.lower() not in {".md", ".txt"}:
        raise HTTPException(status_code=400, detail="Only Markdown and text documents can be edited")
    return {"name": safe_name, "content": path.read_text(encoding="utf-8", errors="ignore")}


@router.post("/api/knowledge/save")
async def api_knowledge_save(request: Request):
    runtime = _runtime(request)
    payload = await request.json()
    name = _sanitize_knowledge_name(str(payload.get("name", "document.md")))
    content = str(payload.get("content", ""))
    if len(content) > 1_000_000:
        raise HTTPException(status_code=413, detail="Document is too large")
    runtime.knowledge.save_document(name, text=content)
    db.log_audit("knowledge_saved", name, actor=request.session.get("user", ""))
    return {"ok": True, "stats": runtime.knowledge.stats()}


@router.post("/api/knowledge/upload")
async def api_knowledge_upload(request: Request):
    runtime = _runtime(request)
    form = await request.form()
    upload = form.get("file")
    if upload is None or not getattr(upload, "filename", ""):
        raise HTTPException(status_code=400, detail="No file uploaded")
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in {".md", ".txt", ".pdf"}:
        raise HTTPException(status_code=400, detail="Only .md, .txt, and .pdf files are supported")
    data = await _read_upload(upload, 25 * 1024 * 1024)
    runtime.knowledge.save_document(upload.filename, data=data)
    db.log_audit("knowledge_uploaded", upload.filename, actor=request.session.get("user", ""))
    return {"ok": True, "stats": runtime.knowledge.stats()}


@router.post("/api/knowledge/reindex")
async def api_knowledge_reindex(request: Request):
    runtime = _runtime(request)
    count = await run_in_threadpool(runtime.knowledge.index)
    db.log_audit("knowledge_reindexed", f"chunks={count}", actor=request.session.get("user", ""))
    return {"ok": True, "chunks": count, "stats": runtime.knowledge.stats()}


@router.get("/api/knowledge/search")
async def api_knowledge_search(request: Request, q: str = ""):
    runtime = _runtime(request)
    return {"results": runtime.knowledge.search(q, k=5)}


# ------------------------------------------------------------------ assistant


@router.post("/api/ask")
async def api_ask(request: Request):
    runtime = _runtime(request)
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    question = str(payload.get("question", "")).strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    if len(question) > 2000:
        raise HTTPException(status_code=400, detail="Question is too long")
    language = "ar" if str(payload.get("language", "en")).lower().startswith("ar") else "en"
    capture = bool(payload.get("capture", True))
    snapshot_path = ""
    if capture:
        snapshot_path, _ = runtime.camera.snapshot_for_event("kiosk")
    answer = await run_in_threadpool(runtime.agent.ask, question, language, True)
    event = runtime.events.log(
        "inquiry",
        "info",
        "Kiosk question answered",
        f"Question: {question}\n\nAnswer: {answer.get('answer', '')}",
        description_ar=f"السؤال: {question}\n\nالإجابة: {answer.get('answer', '')}" if language == "ar" else "",
        snapshot_path=snapshot_path,
        meta={
            "question": question,
            "sources": answer.get("sources", []),
            "provider": answer.get("provider", ""),
            "capture": capture,
            "speak_text": answer.get("answer", "")[:900],
            "speak_language": language,
        },
        translate=False,
    )
    db.log_audit("assistant_question", question[:300], actor=request.session.get("user", ""))
    return {
        "answer": answer.get("answer", ""),
        "sources": answer.get("sources", []),
        "provider": answer.get("provider", ""),
        "snapshot_url": _media_url(snapshot_path),
        "event": _serialize_event(event),
    }


@router.post("/api/assess")
async def api_assess(request: Request):
    runtime = _runtime(request)
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        payload = {}
    language = "ar" if str((payload or {}).get("language", "en")).lower().startswith("ar") else "en"
    result = await run_in_threadpool(runtime.agent.assess, language)
    db.log_audit("risk_assessment", result.get("risk_level", ""), actor=request.session.get("user", ""))
    return result


@router.get("/api/assistant/history")
async def api_assistant_history(request: Request):
    rows = db.fetch_all("SELECT * FROM conversations ORDER BY id DESC LIMIT 12")
    for row in rows:
        try:
            import json

            row["sources"] = json.loads(row.get("sources") or "[]")
        except (TypeError, ValueError):
            row["sources"] = []
    return {"history": rows}


# ------------------------------------------------------------------- settings


@router.get("/api/settings")
async def api_settings(request: Request):
    runtime = _runtime(request)
    settings = db.all_settings()
    safe = {key: value for key, value in settings.items() if key in SETTING_KEYS}
    return {
        "settings": safe,
        "defaults": DEFAULT_SETTINGS,
        "secrets": {
            "openai_configured": bool(OPENAI_API_KEY),
            "libretranslate_configured": bool(os.getenv("LIBRETRANSLATE_URL", "")),
            "vehicle_lookup_configured": bool(os.getenv("VEHICLE_LOOKUP_URL", "")),
        },
        "models": runtime.camera.get_status().get("models", {}),
        "agent": runtime.agent.provider,
    }


@router.put("/api/settings")
async def api_settings_update(request: Request):
    runtime = _runtime(request)
    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid settings payload")
    updated: dict[str, str] = {}
    for key, value in payload.items():
        if key not in SETTING_KEYS:
            continue
        if isinstance(value, bool):
            value = "1" if value else "0"
        value = str(value).strip()
        if len(value) > 500:
            raise HTTPException(status_code=400, detail=f"Value for {key} is too long")
        if key in {"frame_width", "frame_height"}:
            try:
                number = int(float(value))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"{key} must be a number")
            number = max(320, min(1920, number))
            value = str(number)
        if key in {"face_match_threshold", "motion_threshold"}:
            try:
                number = float(value)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"{key} must be a number")
            if key == "face_match_threshold":
                number = max(0.1, min(0.9, number))
            else:
                number = max(0.001, min(0.5, number))
            value = str(number)
        if key in {"detection_interval", "retention_days", "audio_threshold"}:
            try:
                number = float(value)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"{key} must be a number")
            value = str(number)
        db.set_setting(key, value)
        updated[key] = value
    if "camera_source" in updated:
        runtime.camera.switch_source(updated["camera_source"])
    db.log_audit("settings_updated", ", ".join(sorted(updated)), actor=request.session.get("user", ""))
    return {"ok": True, "updated": updated, "restart_camera": "camera_source" in updated}


@router.post("/api/settings/password")
async def api_settings_password(request: Request):
    payload = await request.json()
    current = str(payload.get("current", ""))
    new = str(payload.get("new", ""))
    if len(new) < 10:
        raise HTTPException(status_code=400, detail="The new password must be at least 10 characters.")
    username = request.session.get("user", "")
    user = db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
    if not user or not verify_password(current, user["password_hash"]):
        raise HTTPException(status_code=400, detail="The current password is incorrect.")
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new), user["id"]))
    db.log_audit("password_changed", actor=username)
    return {"ok": True}


@router.post("/api/maintenance/cleanup")
async def api_cleanup(request: Request):
    runtime = _runtime(request)
    removed = await run_in_threadpool(runtime.events.cleanup)
    db.log_audit("retention_cleanup", f"removed={removed}", actor=request.session.get("user", ""))
    return {"ok": True, "removed": removed}


# ------------------------------------------------------------------- audio


@router.post("/api/audio/transcribe")
async def api_audio_transcribe(request: Request):
    runtime = _runtime(request)
    form = await request.form()
    upload = form.get("file")
    if upload is None or not getattr(upload, "filename", ""):
        raise HTTPException(status_code=400, detail="No audio file uploaded")
    data = await _read_upload(upload, 40 * 1024 * 1024)
    result = await run_in_threadpool(runtime.audio.process_uploaded_audio, data, upload.filename)
    result["event"] = _serialize_event(result.get("event"))
    db.log_audit("audio_transcribed", upload.filename, actor=request.session.get("user", ""))
    return result


@router.get("/api/health")
async def api_health(request: Request):
    runtime = _runtime(request)
    status = runtime.camera.get_status()
    return {
        "ok": status.get("running", False),
        "camera": status.get("source"),
        "demo": status.get("demo"),
        "version": APP_VERSION,
    }


@router.post("/api/translate")
async def api_translate(request: Request):
    runtime = _runtime(request)
    payload = await request.json()
    text = str(payload.get("text", ""))[:3000]
    target = str(payload.get("target", "ar"))[:8]
    source = str(payload.get("source", "en"))[:8]
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    translated = await run_in_threadpool(runtime.translator.translate, text, target, source)
    return {"translated": translated, "target": target, "source": source}

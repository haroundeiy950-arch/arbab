from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from ai.agent import SecurityAgent
from ai.face import FaceEngine
from ai.knowledge import KnowledgeBase, seed_knowledge
from ai.translate import TranslationService
from config import APP_NAME, APP_VERSION, HOST, LOG_DIR, PORT, get_secret_key
from core import database as db
from core.events import EventManager
from core.runtime import Runtime
from services.audio_service import AudioService
from services.camera_service import CameraService
from web.alerts import AlertHub
from web.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(LOG_DIR / "sentinel.log", maxBytes=4_000_000, backupCount=3, encoding="utf-8"),
    ],
)
logging.getLogger("ultralytics").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("sentinel")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    seed_knowledge(db.get_setting("company_name", "Arbab Company"))
    hub = AlertHub()
    hub.set_loop(asyncio.get_running_loop())
    translator = TranslationService()
    knowledge = KnowledgeBase()
    agent = SecurityAgent(knowledge, translator)
    events = EventManager(translator, publish=hub.publish)
    face = FaceEngine()
    camera = CameraService(face, translator, events)
    audio = AudioService(events, translator, agent, camera)
    runtime = Runtime(
        translator=translator,
        knowledge=knowledge,
        agent=agent,
        events=events,
        face=face,
        camera=camera,
        audio=audio,
        hub=hub,
    )
    app.state.runtime = runtime
    log.info("Starting %s v%s", APP_NAME, APP_VERSION)
    try:
        await asyncio.to_thread(events.cleanup)
    except Exception:  # noqa: BLE001
        log.exception("Startup retention cleanup failed")
    runtime.start()
    try:
        yield
    finally:
        log.info("Shutting down services")
        await asyncio.to_thread(runtime.shutdown)


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(__import__("pathlib").Path(__file__).resolve().parent / "web" / "static")), name="static")


async def auth_middleware(request, call_next):
    path = request.url.path
    public = (
        path.startswith("/static")
        or path in {"/login", "/api/health", "/favicon.ico"}
    )
    if not public:
        user = None
        try:
            user = request.session.get("user")
        except Exception:  # noqa: BLE001
            user = None
        if not user:
            if path.startswith(("/api/", "/media/")) or path == "/video_feed" or path.startswith("/ws/"):
                return JSONResponse({"detail": "Authentication required"}, status_code=401)
            return RedirectResponse("/login", status_code=303)
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(self), geolocation=()")
    return response


app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=get_secret_key(),
    session_cookie="sentinel_session",
    max_age=12 * 3600,
    same_site="lax",
    https_only=False,
)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    print(f"\n  {APP_NAME} v{APP_VERSION}")
    print(f"  Open http://{HOST}:{PORT} and sign in.\n")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=False, log_level="info")

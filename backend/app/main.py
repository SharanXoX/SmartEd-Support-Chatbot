"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.bootstrap import ensure_admin
from app.config import get_settings, split_origins
from app.database import Base, SessionLocal, engine
from app.paths import DEFAULT_DEMO_ASSETS_DIR, DEFAULT_SUPPORT_ASSETS_DIR
from app.services.support_indexer import get_support_indexer
from app.rate_limit import limiter
from app.ai.provider_factory import get_chat_provider
from app.env_bootstrap import bootstrap_env, env_status
from app.middleware import RequestLoggingMiddleware
from app.routers import admin, auth, chat, debug_routes, demo_routes, ws_chat
from app.services.demo_seed import seed_demo_faqs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("smarted.api")

bootstrap_env()
settings = get_settings()


def _demo_assets_directory() -> pathlib.Path:
    if settings.demo_assets_dir:
        return pathlib.Path(settings.demo_assets_dir).expanduser().resolve()
    return DEFAULT_DEMO_ASSETS_DIR.resolve()


def _support_assets_directory() -> pathlib.Path:
    if settings.support_assets_dir:
        return pathlib.Path(settings.support_assets_dir).expanduser().resolve()
    return DEFAULT_SUPPORT_ASSETS_DIR.resolve()


@asynccontextmanager
async def lifespan(app: FastAPI):
    loaded = bootstrap_env()
    for path in loaded:
        logger.info("[ENV] Loaded %s", path)
    status = env_status()
    sel = get_chat_provider(settings)
    logger.info(
        "[ENV] AI_PROVIDER=%s effective=%s groq_key=%s openai_key=%s",
        status["ai_provider"],
        sel.effective_provider,
        status["groq_api_key_set"],
        status["openai_api_key_set"],
    )
    if sel.error_detail:
        logger.warning("[ENV] Provider note: %s", sel.error_detail)

    pathlib.Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(settings.visual_assets_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    _demo_assets_directory().mkdir(parents=True, exist_ok=True)
    _support_assets_directory().mkdir(parents=True, exist_ok=True)

    count = get_support_indexer().refresh(settings, force=True)
    logger.info("[INDEX] Adaptive support catalog indexed: %d flows", count)
    assets_root = _support_assets_directory()
    for folder in sorted(assets_root.iterdir()) if assets_root.is_dir() else []:
        if folder.is_dir() and not folder.name.startswith("."):
            imgs = list(folder.glob("step*.png")) + list(folder.glob("step*.jpg"))
            logger.info("[INDEX] %s: %d screenshot(s) on disk", folder.name, len(imgs))

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_admin(settings, db)
        seed_demo_faqs(db, settings)
    finally:
        db.close()

    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=split_origins(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(demo_routes.router, prefix="/api")
app.include_router(ws_chat.router)
if settings.enable_debug_routes:
    app.include_router(debug_routes.router)

app.mount("/uploads/visuals", StaticFiles(directory=settings.visual_assets_dir), name="visuals")
app.mount("/demo-assets", StaticFiles(directory=str(_demo_assets_directory())), name="demo_assets")
app.mount(
    "/support-assets",
    StaticFiles(directory=str(_support_assets_directory())),
    name="support_assets",
)


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    """Liveness probe for load balancers and deployment pipelines."""
    return {"status": "healthy", "service": settings.app_name}

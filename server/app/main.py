import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api import admin, auth, devices, health, monzo, read
from app.api.routes import timeline
from app.core.config import get_settings
from app.db.session import Base, engine

settings = get_settings()
logger = logging.getLogger(__name__)
if settings.database_url:
    logger.info("Database configuration detected.")

Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app = FastAPI(title="mentos v0.1 API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(monzo.router)
app.include_router(read.router)
app.include_router(admin.router)
app.include_router(health.router)
app.include_router(timeline.router)

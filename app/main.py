from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import logging

from app.routes.email_routes import email_router
from app.routes.login_routes import login_router
from app.routes.oauth_routes import oauth_router
from app.routes.auth_routes import auth_router
from app.pydantic_schemas.response_pydantic import ResponseSchema

from app.db.dbConnection import engine, SessionLocal
from app.models.base_model import Base
import app.models
from app.routes.queue_routes import queue_router
from app.routes.storage_routes import storage_router
from app.routes.template_routes import template_router
from app.routes.user_routes import user_router
from app.utils.config import settings

from app.services.ratelimiting_services import RateLimitManager
app = FastAPI()

SKIP_PATHS: set[str] = {p.strip() for p in settings.RATE_SKIP_PATHS.split(",") if p.strip()}
HEAVY_PATHS: set[str] = {p.strip() for p in settings.RATE_HEAVY_PATHS.split(",") if p.strip()}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ratelimiter = RateLimitManager(
    rate_per_second=settings.RATE_LIMIT_PER_SECOND,
    capacity=settings.RATE_LIMIT_CAPACITY,
    idle_ttl=settings.RATE_LIMIT_IDLE_TTL,
)

def should_skip(request: Request) -> bool:
    return request.url.path in SKIP_PATHS

def route_cost(request: Request) -> float:
    return settings.RATE_HEAVY_COST if request.url.path in HEAVY_PATHS else settings.RATE_DEFAULT_COST

app.middleware("http")(ratelimiter.middleware(cost_getter=route_cost, skip=should_skip))

app.include_router(oauth_router)
app.include_router(auth_router)
app.include_router(login_router)
app.include_router(user_router)
app.include_router(template_router)
app.include_router(email_router)
app.include_router(queue_router)
app.include_router(storage_router)

@app.on_event("startup")
async def db_create_tables():
    Base.metadata.create_all(bind=engine)

    try:
        db_session = SessionLocal()
        db_session.execute(text('SELECT 1'))
        logger.info("Database connection is successful.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    finally:
        db_session.close()
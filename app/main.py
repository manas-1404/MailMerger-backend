from fastapi import FastAPI, APIRouter
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
from app.routes.template_routes import template_router
from app.routes.user_routes import user_router
from app.utils.config import settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.include_router(oauth_router)
app.include_router(auth_router)
app.include_router(login_router)
app.include_router(user_router)
app.include_router(template_router)
app.include_router(email_router)
app.include_router(queue_router)

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
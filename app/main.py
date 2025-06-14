from fastapi import FastAPI
from sqlalchemy import text
import logging

from app.db.dbConnection import engine, SessionLocal
from app.models.base_model import Base
import app.models
app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

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

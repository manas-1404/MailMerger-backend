from fastapi import FastAPI, APIRouter
from sqlalchemy import text
import logging

from app.routes.oauth_routes import oauth_router
from app.pydantic_schemas.response_pydantic import ResponseSchema

from app.db.dbConnection import engine, SessionLocal
from app.models.base_model import Base
import app.models
app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.include_router(oauth_router)

# @app.get("/")
# async def root():
#     return {"message": "Hello World"}
#
# @app.get("/health")
# async def health_check():
#     return ResponseSchema(
#         status_code=200,
#         message="Service is running",
#         data={"status": "healthy"}
#     )
#
# @app.get("/hello/{name}")
# async def say_hello(name: str):
#     return {"message": f"Hello {name}"}
#
# @app.on_event("startup")
# async def db_create_tables():
#     Base.metadata.create_all(bind=engine)
#
#     try:
#         db_session = SessionLocal()
#         db_session.execute(text('SELECT 1'))
#         logger.info("Database connection is successful.")
#     except Exception as e:
#         logger.error(f"Database connection failed: {e}")
#     finally:
#         db_session.close()

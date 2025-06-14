from fastapi import FastAPI

from app.db.dbConnection import engine
from app.models.base_model import Base
import app.models
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@app.on_event("startup")
async def db_create_tables():
    Base.metadata.create_all(bind=engine)

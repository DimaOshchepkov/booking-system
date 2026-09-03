from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.core.config import settings
from app.database import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()

app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World", "debug": settings.DEBUG}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}